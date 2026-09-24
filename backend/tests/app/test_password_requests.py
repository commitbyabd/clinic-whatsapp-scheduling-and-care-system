"""
Tests for "forgot your password": the note a stuck staff member leaves at
the sign-in page, and the admin's list of them.

The thing being protected is that the form hands nothing back. Whatever is
typed, the reply is the same, and no password changes — an admin does the
reset by hand.

The in-memory fake in fake_mongo.py stands in for MongoDB, so these need no
database.

    python tests/app/test_password_requests.py
    pytest
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.features.admin.v1 import close_password_request as close  # noqa: E402
from app.features.admin.v1 import get_password_requests as listing  # noqa: E402
from app.features.admin.v1 import reset_staff_password as reset  # noqa: E402
from app.features.auth.v1 import request_password_help as help_request  # noqa: E402
from fake_mongo import FakeCollection, FakeDatabase  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
MODULES = (help_request, listing, close, reset)

ADMIN_ID = ObjectId()

DOCTOR = {
    "_id": ObjectId(),
    "full_name": "Dr. Sara Khan",
    "email": "sara@clinic.com",
    "role": "doctor",
    "is_active": True,
}
RECEPTIONIST = {
    "_id": ObjectId(),
    "full_name": "Ayesha Malik",
    "email": "ayesha@clinic.com",
    "role": "receptionist",
    "is_active": True,
}
ADMIN = {
    "_id": ADMIN_ID,
    "full_name": "Clinic Admin",
    "email": "admin@clinic.com",
    "role": "admin",
    "is_active": True,
}

STAFF = (DOCTOR, RECEPTIONIST, ADMIN)


def _reply(coroutine):
    response = asyncio.run(coroutine)
    return response.status_code, json.loads(response.body)


def _database(users=STAFF, requests=()):
    return FakeDatabase(MODULES, users=users, password_requests=requests)


def _ask(email, db):
    with db:
        return _reply(help_request.request_password_help(email))


def _request_row(user=DOCTOR, **changes):
    return {
        "_id": ObjectId(),
        "user_id": user["_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "status": "new",
        "times_asked": 1,
        "asked_at": datetime(2026, 9, 24, 9, 30, tzinfo=timezone.utc),
        "created_at": datetime(2026, 9, 24, 9, 30, tzinfo=timezone.utc),
        **changes,
    }


# --- what the person at the sign-in page gets --------------------------


def test_a_staff_email_leaves_a_note_for_the_admin():
    db = _database()
    status, body = _ask("sara@clinic.com", db)

    assert status == 200, body
    # the envelope sends [] for no data: nothing about the account goes back
    assert body["data"] == [], body

    rows = db.password_requests.docs
    assert len(rows) == 1, rows
    assert rows[0]["user_id"] == DOCTOR["_id"]
    assert rows[0]["full_name"] == "Dr. Sara Khan"
    assert rows[0]["role"] == "doctor"
    assert rows[0]["status"] == "new"
    assert rows[0]["times_asked"] == 1


def test_an_unknown_email_leaves_nothing_and_reads_the_same():
    known = _database()
    unknown = _database()

    _, from_staff = _ask("sara@clinic.com", known)
    status, from_stranger = _ask("someone@example.com", unknown)

    assert status == 200, from_stranger
    assert unknown.password_requests.docs == [], "a stranger filled the list"
    # the giveaway would be a different answer
    assert from_stranger["message"] == from_staff["message"]


def test_the_email_is_matched_however_it_is_typed():
    db = _database()
    _ask("  SARA@Clinic.com ", db)
    assert len(db.password_requests.docs) == 1, db.password_requests.docs


def test_an_account_nobody_can_reset_leaves_nothing():
    """An admin's password is not reset from the portal, and a deactivated
    account is shut out on purpose. Both read the same as any other."""
    gone = {**DOCTOR, "_id": ObjectId(), "email": "old@clinic.com",
            "is_active": False}
    db = _database(users=(DOCTOR, ADMIN, gone))

    _, for_admin = _ask("admin@clinic.com", db)
    _, for_gone = _ask("old@clinic.com", db)
    _, for_staff = _ask("sara@clinic.com", db)

    assert [row["email"] for row in db.password_requests.docs] == [
        "sara@clinic.com"
    ], db.password_requests.docs
    assert for_admin["message"] == for_staff["message"] == for_gone["message"]


def test_asking_again_bumps_the_count_instead_of_adding_a_row():
    db = _database()
    _ask("sara@clinic.com", db)
    _ask("sara@clinic.com", db)
    _ask("sara@clinic.com", db)

    rows = db.password_requests.docs
    assert len(rows) == 1, rows
    assert rows[0]["times_asked"] == 3, rows[0]


def test_a_new_ask_after_one_was_handled_starts_a_new_row():
    handled = _request_row(status="handled")
    db = _database(requests=[handled])
    _ask("sara@clinic.com", db)

    waiting = [row for row in db.password_requests.docs if row["status"] == "new"]
    assert len(waiting) == 1, db.password_requests.docs
    assert len(db.password_requests.docs) == 2, "the handled one was overwritten"


def test_a_database_fault_says_so_without_details():
    db = FakeDatabase(
        MODULES, users=FakeCollection(error=RuntimeError("cluster0 unreachable"))
    )
    with db:
        status, body = _reply(help_request.request_password_help("sara@clinic.com"))

    assert status == 500, body
    assert body["error_code"] == "PASSWORD_HELP_FAILED"
    assert "cluster0" not in json.dumps(body), body


def test_the_email_typed_never_reaches_the_logs():
    """A staff email is personal data, and an unknown one may be a patient's."""
    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = _Capture()
    root = logging.getLogger()
    root.addHandler(handler)
    previous = root.level
    root.setLevel(logging.DEBUG)
    try:
        _ask("stranger@example.com", _database())
        _ask("sara@clinic.com", _database())
    finally:
        root.removeHandler(handler)
        root.setLevel(previous)

    logged = "\n".join(records)
    assert "stranger@example.com" not in logged, logged
    assert "sara@clinic.com" not in logged, logged


def test_the_form_needs_no_token_and_refuses_a_bad_address():
    # whoever needs this cannot sign in, so there is no token to send
    refused = client.post("/auth/password-help", json={"email": "not-an-email"})
    assert refused.status_code == 422, refused.text
    assert refused.status_code != 401


# --- the admin's list --------------------------------------------------


def test_the_list_holds_what_the_admin_needs_and_no_more():
    with _database(requests=[_request_row()]):
        status, body = _reply(listing.get_password_requests())

    assert status == 200, body
    row = body["data"][0]
    assert row["full_name"] == "Dr. Sara Khan"
    assert row["email"] == "sara@clinic.com"
    assert row["role"] == "doctor"
    assert row["user_id"] == str(DOCTOR["_id"])
    assert row["asked_at"].startswith("2026-09-24T09:30")
    # bookkeeping stays in the database
    assert "status" not in row and "handled_by" not in row, row


def test_only_the_ones_still_waiting_are_listed():
    handled = _request_row(RECEPTIONIST, status="handled")
    with _database(requests=[_request_row(), handled]) as db:
        status, body = _reply(listing.get_password_requests())

    assert status == 200, body
    assert [row["full_name"] for row in body["data"]] == ["Dr. Sara Khan"]
    assert db.password_requests.queries[0] == {"status": "new"}


def test_the_newest_ask_is_first():
    older = _request_row(
        RECEPTIONIST, asked_at=datetime(2026, 9, 24, 8, 0, tzinfo=timezone.utc)
    )
    with _database(requests=[older, _request_row()]):
        _, body = _reply(listing.get_password_requests())

    assert [row["full_name"] for row in body["data"]] == [
        "Dr. Sara Khan",
        "Ayesha Malik",
    ], body["data"]


def test_an_empty_list_is_not_an_error():
    with _database():
        status, body = _reply(listing.get_password_requests())
    assert status == 200 and body["data"] == [], body


# --- closing one -------------------------------------------------------


def test_dismissing_takes_it_off_the_list():
    row = _request_row()
    with _database(requests=[row]) as db:
        status, body = _reply(
            close.close_password_request(str(row["_id"]), str(ADMIN_ID))
        )

    assert status == 200, body
    stored = db.password_requests.docs[0]
    assert stored["status"] == "handled"
    assert stored["handled_by"] == ADMIN_ID
    assert isinstance(stored["handled_at"], datetime)


def test_closing_one_that_is_already_done_is_a_404():
    row = _request_row(status="handled")
    with _database(requests=[row]):
        status, body = _reply(
            close.close_password_request(str(row["_id"]), str(ADMIN_ID))
        )
    assert status == 404 and body["error_code"] == "PASSWORD_REQUEST_NOT_FOUND"


def test_a_malformed_request_id_is_a_400():
    with _database():
        status, body = _reply(close.close_password_request("nope", str(ADMIN_ID)))
    assert status == 400 and body["error_code"] == "INVALID_REQUEST_ID"


def test_resetting_the_password_answers_the_request():
    """However the admin got there: the reset is the answer."""
    row = _request_row()
    other = _request_row(RECEPTIONIST)
    db = _database(requests=[row, other])

    with db:
        status, body = _reply(
            reset.reset_staff_password(
                str(DOCTOR["_id"]), "a new password", str(ADMIN_ID)
            )
        )

    assert status == 200, body
    closed, untouched = db.password_requests.docs
    assert closed["status"] == "handled" and closed["handled_by"] == ADMIN_ID
    assert untouched["status"] == "new", "someone else's request was closed"


def test_a_reset_still_works_if_the_request_cannot_be_closed():
    """The password is what matters; the list is bookkeeping."""
    requests = FakeCollection(
        [_request_row()], update_error=RuntimeError("cluster0 unreachable")
    )
    with FakeDatabase(MODULES, users=STAFF, password_requests=requests):
        status, body = _reply(
            reset.reset_staff_password(
                str(DOCTOR["_id"]), "a new password", str(ADMIN_ID)
            )
        )

    assert status == 200, body


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}\n  {exc}\n")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} test functions passed")
    sys.exit(1 if failed else 0)
