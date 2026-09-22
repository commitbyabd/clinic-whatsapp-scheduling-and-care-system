"""
Tests for the front desk's booked appointments: a day's list, cancelling
with a reason, moving a visit to another time or doctor, and declining a
request with a reason.

The in-memory fake in fake_mongo.py stands in for MongoDB.

    python tests/app/test_reception_appointments.py
    pytest
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo.errors import DuplicateKeyError  # noqa: E402

from app.core.clinic_time import CLINIC_TZ, clinic_time  # noqa: E402
from app.features.receptionist.v1 import cancel_appointment as cancel  # noqa: E402
from app.features.receptionist.v1 import decline_booking_request as decline  # noqa: E402
from app.features.receptionist.v1 import get_day_appointments as day_list  # noqa: E402
from app.features.receptionist.v1 import get_free_slots as slots  # noqa: E402
from app.features.receptionist.v1 import reschedule_appointment as move  # noqa: E402
from fake_mongo import FakeCollection, FakeDatabase  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
UTC = timezone.utc
MODULES = (cancel, decline, day_list, slots, move)

DAY = (datetime.now(CLINIC_TZ) + timedelta(days=3)).date()
RECEPTIONIST_ID = ObjectId()


def _at(hhmm, day=DAY):
    return clinic_time(day, hhmm).astimezone(UTC)


DOCTOR = {"_id": ObjectId(), "full_name": "Dr. Sara Khan", "role": "doctor",
          "specialization": "Dermatologist", "is_active": True}
OTHER_DOCTOR = {"_id": ObjectId(), "full_name": "Dr. Usman", "role": "doctor",
                "specialization": "Cardiologist", "is_active": True}
WEEK = [{"day_of_week": d, "start_time": "09:00", "end_time": "12:00"} for d in range(7)]
SCHEDULES = [
    {"_id": ObjectId(), "doctor_id": doctor["_id"], "working_hours": WEEK,
     "slot_minutes": 30, "blackout_dates": [], "is_active": True}
    for doctor in (DOCTOR, OTHER_DOCTOR)
]
PATIENT = {"_id": ObjectId(), "full_name": "Ayesha Khan",
           "whatsapp_number": "+923001234567", "allergies": ["Penicillin"]}
VISIT = {
    "_id": ObjectId(), "doctor_id": DOCTOR["_id"], "patient_id": PATIENT["_id"],
    "scheduled_for": _at("10:00"), "duration_minutes": 30, "status": "booked",
    "reason": "symptoms", "symptom_summary": "blisters on my feet",
    "doctor_snapshot": {"full_name": "Dr. Sara Khan"}, "specialization": "Dermatologist",
}


def _reply(coroutine):
    response = asyncio.run(coroutine)
    return response.status_code, json.loads(response.body)


def _database(visits=(VISIT,), **collections):
    return FakeDatabase(MODULES, **{
        "appointments": visits,
        "patients": [PATIENT],
        "users": [DOCTOR, OTHER_DOCTOR],
        "schedules": SCHEDULES,
        **collections,
    })


def _move(to, doctor=DOCTOR, visit=VISIT):
    payload = {
        "appointment_id": str(visit["_id"]),
        "receptionist_id": str(RECEPTIONIST_ID),
        "doctor_id": str(doctor["_id"]),
        "starts_at": to,
    }
    return _reply(move.reschedule_appointment(payload))


# ---------------------------------------------------------------- the day


def test_a_day_lists_every_doctors_visits_in_time_order():
    early = {**VISIT, "_id": ObjectId(), "doctor_id": OTHER_DOCTOR["_id"],
             "scheduled_for": _at("09:00"), "doctor_snapshot": {"full_name": "Dr. Usman"}}
    cancelled = {**VISIT, "_id": ObjectId(), "scheduled_for": _at("11:00"),
                 "status": "cancelled", "cancel_reason": "patient travelling"}
    next_day = {**VISIT, "_id": ObjectId(), "scheduled_for": _at("10:00", DAY + timedelta(days=1))}

    with _database(visits=[VISIT, early, cancelled, next_day]):
        code, body = _reply(day_list.get_day_appointments(DAY))

    assert code == 200, body
    rows = body["data"]
    assert [row["id"] for row in rows] == [str(early["_id"]), str(VISIT["_id"]), str(cancelled["_id"])]
    first = rows[1]
    assert first["doctor"]["full_name"] == "Dr. Sara Khan"
    assert first["patient"] == {"id": str(PATIENT["_id"]), "full_name": "Ayesha Khan",
                                "whatsapp_number": "+923001234567"}
    assert rows[2]["cancel_reason"] == "patient travelling"
    # the front desk sees who and when, nothing clinical
    assert "symptom_summary" not in first and "allergies" not in first["patient"], first


def test_an_empty_day_is_not_an_error():
    with _database(visits=[]):
        code, body = _reply(day_list.get_day_appointments(DAY))
    assert code == 200 and body["data"] == [], body


# ------------------------------------------------------------- cancelling


def test_cancelling_keeps_the_visit_with_its_reason():
    with _database() as db:
        code, body = _reply(cancel.cancel_appointment(
            str(VISIT["_id"]), str(RECEPTIONIST_ID), "patient travelling"))
    assert code == 200 and body["data"]["status"] == "cancelled", body
    saved = db.appointments.docs[0]
    assert saved["cancel_reason"] == "patient travelling"
    assert saved["cancelled_by"] == RECEPTIONIST_ID and saved["cancelled_at"] is not None


def test_a_visit_that_has_happened_cannot_be_cancelled():
    with _database(visits=[{**VISIT, "status": "completed"}]):
        code, body = _reply(cancel.cancel_appointment(str(VISIT["_id"]), str(RECEPTIONIST_ID), None))
    assert (code, body["error_code"]) == (409, "APPOINTMENT_NOT_CANCELLABLE"), body


def test_cancelling_an_unknown_visit_is_404():
    with _database():
        code, body = _reply(cancel.cancel_appointment(str(ObjectId()), str(RECEPTIONIST_ID), None))
        bad, _ = _reply(cancel.cancel_appointment("not-an-id", str(RECEPTIONIST_ID), None))
    assert (code, body["error_code"]) == (404, "APPOINTMENT_NOT_FOUND"), body
    assert bad == 400


# ------------------------------------------------------------ rescheduling


def test_moving_a_visit_to_another_free_time():
    with _database(visits=[{**VISIT, "status": "confirmed"}]) as db:
        code, body = _move(_at("11:00"))
    assert code == 200, body
    saved = db.appointments.docs[0]
    assert saved["scheduled_for"] == _at("11:00")
    # a new time the patient has not agreed to yet
    assert saved["status"] == "booked"
    assert saved["rescheduled_by"] == RECEPTIONIST_ID


def test_moving_a_visit_to_another_doctor():
    with _database() as db:
        code, body = _move(_at("09:30"), doctor=OTHER_DOCTOR)
    assert code == 200, body
    saved = db.appointments.docs[0]
    assert saved["doctor_id"] == OTHER_DOCTOR["_id"]
    assert saved["doctor_snapshot"] == {"full_name": "Dr. Usman"}
    assert saved["specialization"] == "Cardiologist"


def test_a_visit_is_not_blocked_by_its_own_old_time():
    # an hour-long visit at 10:00 moved to 10:30 overlaps where it is now
    long_visit = {**VISIT, "duration_minutes": 60}
    with _database(visits=[long_visit]):
        code, body = _move(_at("10:30"), visit=long_visit)
    assert code == 200, body


def test_a_taken_time_is_refused():
    other = {**VISIT, "_id": ObjectId(), "scheduled_for": _at("11:00")}
    with _database(visits=[VISIT, other]) as db:
        code, body = _move(_at("11:00"))
        assert (code, body["error_code"]) == (409, "SLOT_NOT_FREE"), body
        assert db.appointments.docs[0]["scheduled_for"] == _at("10:00")


def test_a_time_booked_at_the_same_moment_is_refused():
    collection = FakeCollection([VISIT], update_error=DuplicateKeyError("E11000 duplicate key"))
    with _database(appointments=collection):
        code, body = _move(_at("11:00"))
    assert (code, body["error_code"]) == (409, "SLOT_NOT_FREE"), body


def test_a_cancelled_or_unknown_visit_cannot_be_moved():
    with _database(visits=[{**VISIT, "status": "cancelled"}]):
        code, body = _move(_at("11:00"))
    with _database(visits=[]):
        missing, missing_body = _move(_at("11:00"))
    assert (code, body["error_code"]) == (409, "APPOINTMENT_NOT_MOVABLE"), body
    assert (missing, missing_body["error_code"]) == (404, "APPOINTMENT_NOT_FOUND")


# ---------------------------------------------------------------- declining


def test_declining_keeps_the_reason():
    request = {"_id": ObjectId(), "status": "new", "whatsapp_number": "+923001234567"}
    with _database(booking_requests=[request]) as db:
        code, body = _reply(decline.decline_booking_request(
            str(request["_id"]), str(RECEPTIONIST_ID), "booked by phone instead"))
    assert code == 200, body
    assert db.booking_requests.docs[0]["decline_reason"] == "booked by phone instead"


def test_the_new_routes_need_a_signed_in_receptionist():
    visit_id = str(VISIT["_id"])
    responses = [
        client.get("/receptionist/appointments", params={"date": DAY.isoformat()}),
        client.patch(f"/receptionist/appointments/{visit_id}/cancel", json={"reason": "x"}),
        client.patch(
            f"/receptionist/appointments/{visit_id}/reschedule",
            json={"doctor_id": str(DOCTOR["_id"]), "starts_at": _at("11:00").isoformat()},
        ),
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
