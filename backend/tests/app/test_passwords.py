"""
Tests for staff passwords: changing your own, an admin resetting one, and
sessions ending when either happens or when an account is deactivated.

The in-memory fake in fake_mongo.py stands in for MongoDB. Passwords are
hashed with real bcrypt, so these take a couple of seconds.

    python tests/app/test_passwords.py
    pytest
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bson import ObjectId  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.core.security import (  # noqa: E402
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.dependencies import auth as dependency  # noqa: E402
from app.features.admin.v1 import reset_staff_password as reset  # noqa: E402
from app.features.auth.v1 import change_password as change  # noqa: E402
from app.schemas.password_update import PasswordChange  # noqa: E402
from fake_mongo import FakeCollection, FakeDatabase  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
MODULES = (change, reset, dependency)

OLD = "old password 1"
NEW = "new password 2"

DOCTOR = {
    "_id": ObjectId(),
    "full_name": "Dr. Sara Khan",
    "role": "doctor",
    "is_active": True,
    "password_hash": hash_password(OLD),
}
ADMIN = {**DOCTOR, "_id": ObjectId(), "full_name": "Admin", "role": "admin"}


def _reply(coroutine):
    response = asyncio.run(coroutine)
    return response.status_code, json.loads(response.body)


def _database(users=(DOCTOR, ADMIN)):
    return FakeDatabase(MODULES, users=users)


def _signed_in(token):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return asyncio.run(dependency.get_current_user(credentials))


def _refused(token):
    try:
        _signed_in(token)
    except HTTPException as exc:
        return exc.status_code == 401
    return False


# ---------------------------------------------------------- your own password


def test_changing_your_password_stores_it_and_keeps_you_signed_in():
    with _database() as db:
        code, body = _reply(change.change_password(DOCTOR, OLD, NEW))
        saved = db.users.docs[0]

        assert code == 200, body
        assert verify_password(NEW, saved["password_hash"])
        assert saved["password_changed_at"] is not None
        # the fresh token belongs to the same person and still works
        payload = decode_access_token(body["data"]["access_token"])
        assert payload["sub"] == str(DOCTOR["_id"]) and payload["role"] == "doctor"
        assert _signed_in(body["data"]["access_token"])["_id"] == DOCTOR["_id"]


def test_a_wrong_current_password_changes_nothing():
    with _database() as db:
        code, body = _reply(change.change_password(DOCTOR, "not it", NEW))
        assert (code, body["error_code"]) == (400, "WRONG_PASSWORD"), body
        assert verify_password(OLD, db.users.docs[0]["password_hash"])


def test_the_new_password_must_differ():
    with _database():
        code, body = _reply(change.change_password(DOCTOR, OLD, OLD))
    assert (code, body["error_code"]) == (400, "SAME_PASSWORD"), body


def test_the_new_password_has_the_same_limits_as_a_new_account():
    for short in ("", "seven77"):
        try:
            PasswordChange.model_validate({"current_password": OLD, "new_password": short})
        except ValidationError:
            continue
        raise AssertionError(f"accepted {short!r}")


# ------------------------------------------------------------ admin resets


def test_an_admin_resets_a_staff_password():
    with _database() as db:
        code, body = _reply(reset.reset_staff_password(str(DOCTOR["_id"]), NEW))
        saved = db.users.docs[0]
    assert code == 200, body
    assert verify_password(NEW, saved["password_hash"])
    assert saved["password_changed_at"] is not None


def test_another_admins_password_is_not_reset_here():
    with _database() as db:
        code, body = _reply(reset.reset_staff_password(str(ADMIN["_id"]), NEW))
        assert (code, body["error_code"]) == (404, "USER_NOT_FOUND"), body
        assert verify_password(OLD, db.users.docs[1]["password_hash"])


def test_a_malformed_id_is_a_400():
    with _database():
        code, body = _reply(reset.reset_staff_password("not-an-id", NEW))
    assert (code, body["error_code"]) == (400, "INVALID_USER_ID"), body


# ------------------------------------------------------------ sessions


def test_a_session_from_before_a_password_change_ends():
    token = create_access_token(str(DOCTOR["_id"]), "doctor")
    later = datetime.now(timezone.utc) + timedelta(minutes=1)
    with _database(users=[{**DOCTOR, "password_changed_at": later.replace(tzinfo=None)}]):
        assert _refused(token)


def test_a_session_after_the_change_carries_on():
    earlier = datetime.now(timezone.utc) - timedelta(minutes=1)
    with _database(users=[{**DOCTOR, "password_changed_at": earlier.replace(tzinfo=None)}]):
        token = create_access_token(str(DOCTOR["_id"]), "doctor")
        assert _signed_in(token)["_id"] == DOCTOR["_id"]


def test_a_deactivated_account_is_shut_out_at_once():
    # not only at the next sign in: a token already issued stops working
    token = create_access_token(str(DOCTOR["_id"]), "doctor")
    with _database(users=[{**DOCTOR, "is_active": False}]):
        assert _refused(token)


def test_the_password_routes_need_a_signed_in_user():
    responses = [
        client.post(
            "/auth/change-password",
            json={"current_password": OLD, "new_password": NEW},
        ),
        client.put(f"/admin/staff/{DOCTOR['_id']}/password", json={"new_password": NEW}),
    ]
    assert all(response.status_code in (401, 403) for response in responses), [
        response.status_code for response in responses
    ]


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
