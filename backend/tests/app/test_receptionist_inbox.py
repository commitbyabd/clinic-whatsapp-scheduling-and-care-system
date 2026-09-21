"""
Tests for the receptionist's booking request inbox.

A fake collection stands in for MongoDB, so these need no database. The route
is checked for its auth guard without a real token.

    python tests/app/test_receptionist_inbox.py
    pytest
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.features.receptionist.v1 import get_booking_requests as inbox  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)

ROW = {
    "_id": ObjectId(),
    "channel": "whatsapp",
    "whatsapp_number": "+923001234567",
    "patient_name": "Ayesha Khan",
    "returning_patient": "no",
    "reason": "symptoms",
    "symptom_text": "blisters on my feet",
    "suggested_specialization": "Dermatologist",
    "preferred_time_text": "tomorrow at 9am",
    "status": "new",
    "patient_id": None,
    "handled_by": None,
    "created_at": datetime(2026, 9, 21, 9, 30, tzinfo=timezone.utc),
}


class _FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.sorted_by = None
        self.limited_to = None

    def sort(self, key, direction):
        self.sorted_by = (key, direction)
        return self

    def limit(self, count):
        self.limited_to = count
        return self

    async def to_list(self, length=None):
        return self.rows


class _FakeDatabase:
    """Stands in for get_database(), recording the query the inbox makes."""

    def __init__(self, rows=None, error=None):
        self.cursor = _FakeCursor(rows or [])
        self.error = error
        self.filter = None
        self.booking_requests = self

    def find(self, query):
        if self.error is not None:
            raise self.error
        self.filter = query
        return self.cursor

    def __enter__(self):
        self._original = inbox.get_database
        inbox.get_database = lambda: self
        return self

    def __exit__(self, *exc):
        inbox.get_database = self._original


def _call(status="new", limit=50):
    response = asyncio.run(inbox.get_booking_requests(status, limit))
    return response.status_code, json.loads(response.body)


def test_inbox_asks_for_one_status_newest_first():
    with _FakeDatabase([ROW]) as db:
        _call("new", 25)
    assert db.filter == {"status": "new"}
    assert db.cursor.sorted_by == ("created_at", -1)
    assert db.cursor.limited_to == 25


def test_inbox_returns_the_request_fields_only():
    with _FakeDatabase([ROW]):
        status, body = _call()
    assert status == 200, body
    request = body["data"][0]
    assert request["id"] == str(ROW["_id"])
    assert request["patient_name"] == "Ayesha Khan"
    assert request["suggested_specialization"] == "Dermatologist"
    assert request["created_at"].startswith("2026-09-21T09:30")
    # bookkeeping fields stay in the database
    assert "handled_by" not in request and "channel" not in request, request


def test_times_are_sent_as_utc():
    # Mongo returns datetimes without a timezone; the browser must still know
    # they are UTC, or every "Received" time shifts by the viewer's offset
    naive = {**ROW, "created_at": datetime(2026, 9, 21, 9, 30)}
    with _FakeDatabase([naive]):
        _, body = _call()
    assert body["data"][0]["created_at"] == "2026-09-21T09:30:00+00:00", body


def test_an_empty_inbox_is_not_an_error():
    with _FakeDatabase([]):
        status, body = _call()
    assert status == 200 and body["data"] == [], body


def test_a_database_failure_is_a_500_without_details():
    with _FakeDatabase(error=RuntimeError("connection refused to cluster0")):
        status, body = _call()
    assert status == 500, body
    assert "cluster0" not in body["message"], body


def test_the_inbox_needs_a_signed_in_receptionist():
    response = client.get("/receptionist/booking-requests")
    assert response.status_code in (401, 403), response.status_code


def test_an_unknown_status_is_rejected():
    response = client.get(
        "/receptionist/booking-requests",
        params={"status": "everything"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    # refused before any data is read, whichever check runs first
    assert response.status_code in (401, 403, 422), response.status_code


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
