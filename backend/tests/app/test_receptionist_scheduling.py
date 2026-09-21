"""
Tests for receptionist scheduling: free slots, matching patients, booking a
request into an appointment, and declining one.

A small in-memory fake stands in for MongoDB, so these need no database.
The transaction is replaced by a plain call, and the fake records the
session each write was given, to check every write joins the transaction.

    python tests/app/test_receptionist_scheduling.py
    pytest
"""

import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from pymongo.errors import DuplicateKeyError  # noqa: E402

from app.core.clinic_time import CLINIC_TZ, clinic_time  # noqa: E402
from app.features.receptionist.v1 import decline_booking_request as decline  # noqa: E402
from app.features.receptionist.v1 import get_doctors as doctors  # noqa: E402
from app.features.receptionist.v1 import get_free_slots as slots  # noqa: E402
from app.features.receptionist.v1 import get_matching_patients as matching  # noqa: E402
from app.features.receptionist.v1 import schedule_booking_request as scheduling  # noqa: E402
from app.schemas.booking_schedule import BookingSchedule  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
UTC = timezone.utc

# a Monday, for the tests that pass their own "now"
MONDAY = date(2026, 9, 28)
LONG_AGO = datetime(2026, 1, 1, tzinfo=UTC)

# far enough ahead that every slot on it is still in the future
DAY = (datetime.now(CLINIC_TZ) + timedelta(days=3)).date()
SLOT = clinic_time(DAY, "10:00").astimezone(UTC)
SESSION = object()

RECEPTIONIST_ID = ObjectId()
DOCTOR = {
    "_id": ObjectId(),
    "full_name": "Dr. Sara Khan",
    "email": "sara@clinic.com",
    "role": "doctor",
    "specialization": "Dermatologist",
    "is_active": True,
}
SCHEDULE = {
    "_id": ObjectId(),
    "doctor_id": DOCTOR["_id"],
    "working_hours": [
        {"day_of_week": day, "start_time": "09:00", "end_time": "12:00"}
        for day in range(7)
    ],
    "slot_minutes": 30,
    "blackout_dates": [],
    "is_active": True,
}
REQUEST = {
    "_id": ObjectId(),
    "channel": "whatsapp",
    "whatsapp_number": "+923001234567",
    "patient_name": "Ayesha Khan",
    "returning_patient": "no",
    "reason": "symptoms",
    "symptom_text": "blisters on my feet",
    "suggested_specialization": "Dermatologist",
    "preferred_time_text": "Thursday at 10am",
    "status": "new",
    "patient_id": None,
    "appointment_id": None,
    "handled_by": None,
    "handled_at": None,
    "created_at": datetime(2026, 9, 21, 9, 30),
}
PATIENT = {
    "_id": ObjectId(),
    "full_name": "Ayesha Khan",
    "whatsapp_number": "+923001234567",
    # Mongo returns datetimes without a timezone
    "date_of_birth": datetime(1998, 5, 4),
    "gender": "female",
    "allergies": ["penicillin"],
    "is_active": True,
}


def _week(start="09:00", end="12:00", minutes=30, **changes):
    return {
        "working_hours": [{"day_of_week": 0, "start_time": start, "end_time": end}],
        "slot_minutes": minutes,
        "blackout_dates": [],
        **changes,
    }


def _clock(day, hhmm):
    return clinic_time(day, hhmm).astimezone(UTC)


# --------------------------------------------------------------- fake Mongo


def _utc(value):
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _matches(doc, query):
    for field, wanted in query.items():
        value = _utc(doc.get(field))
        if isinstance(wanted, dict):
            for op, operand in wanted.items():
                if op == "$in" and value not in operand:
                    return False
                if op == "$gte" and (value is None or value < operand):
                    return False
                if op == "$lt" and (value is None or value >= operand):
                    return False
        elif value != wanted:
            return False
    return True


class _FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, key, direction):
        self.rows.sort(key=lambda row: row.get(key), reverse=direction == -1)
        return self

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    async def to_list(self, length=None):
        return self.rows


class _FakeCollection:
    def __init__(self, docs=(), error=None, insert_error=None):
        self.docs = [dict(doc) for doc in docs]
        self.error = error
        self.insert_error = insert_error
        self.inserted = []
        self.queries = []
        # the session each write was given
        self.write_sessions = []

    def _check(self, query):
        if self.error is not None:
            raise self.error
        self.queries.append(query)

    async def find_one(self, query, projection=None, session=None):
        self._check(query)
        return next((dict(doc) for doc in self.docs if _matches(doc, query)), None)

    def find(self, query, projection=None, session=None):
        self._check(query)
        return _FakeCursor([dict(doc) for doc in self.docs if _matches(doc, query)])

    async def insert_one(self, doc, session=None):
        if self.insert_error is not None:
            raise self.insert_error
        self.write_sessions.append(session)
        self.docs.append(dict(doc))
        self.inserted.append(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    async def update_one(self, query, update, session=None):
        self._check(query)
        self.write_sessions.append(session)
        for doc in self.docs:
            if _matches(doc, query):
                doc.update(update["$set"])
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    async def find_one_and_update(self, query, update, return_document=None, session=None):
        self._check(query)
        for doc in self.docs:
            if _matches(doc, query):
                doc.update(update["$set"])
                return dict(doc)
        return None


MODULES = (decline, doctors, slots, matching, scheduling)


class _FakeDatabase:
    """Stands in for get_database() in every scheduling module."""

    def __init__(self, requests=(REQUEST,), appointments=(), patients=(PATIENT,),
                 users=(DOCTOR,), schedules=(SCHEDULE,), **collections):
        self.booking_requests = _FakeCollection(requests)
        self.appointments = _FakeCollection(appointments)
        self.patients = _FakeCollection(patients)
        self.users = _FakeCollection(users)
        self.schedules = _FakeCollection(schedules)
        for name, collection in collections.items():
            setattr(self, name, collection)
        self.transactions = 0

    async def _transaction(self, work):
        self.transactions += 1
        return await work(SESSION)

    def __enter__(self):
        self._originals = [(module, module.get_database) for module in MODULES]
        for module in MODULES:
            module.get_database = lambda: self
        self._original_transaction = scheduling.run_in_transaction
        scheduling.run_in_transaction = self._transaction
        return self

    def __exit__(self, *exc):
        for module, original in self._originals:
            module.get_database = original
        scheduling.run_in_transaction = self._original_transaction


def _reply(coroutine):
    response = asyncio.run(coroutine)
    return response.status_code, json.loads(response.body)


def _schedule(**changes):
    payload = {
        "request_id": str(REQUEST["_id"]),
        "receptionist_id": str(RECEPTIONIST_ID),
        "doctor_id": str(DOCTOR["_id"]),
        "starts_at": SLOT,
        "patient_id": None,
        "new_patient": {"full_name": "Ayesha Khan", "date_of_birth": date(1998, 5, 4), "gender": "female"},
        **changes,
    }
    return _reply(scheduling.schedule_booking_request(payload))


# ------------------------------------------------------ working out the slots


def test_slots_follow_the_working_hours_in_clinic_time():
    starts, closed = slots.working_slots(_week("09:00", "11:00"), MONDAY)
    assert closed is None
    # 09:00 in Pakistan is 04:00 UTC
    assert starts[0] == datetime(2026, 9, 28, 4, 0, tzinfo=UTC), starts
    assert len(starts) == 4, starts


def test_a_slot_must_end_by_the_end_of_its_block():
    starts, _ = slots.working_slots(_week("09:00", "10:00", minutes=25), MONDAY)
    # 09:50 would run to 10:15, past the end of the block
    assert starts == [_clock(MONDAY, "09:00"), _clock(MONDAY, "09:25")], starts


def test_a_day_can_have_two_blocks():
    week = _week()
    week["working_hours"] = [
        {"day_of_week": 0, "start_time": "17:00", "end_time": "18:00"},
        {"day_of_week": 0, "start_time": "09:00", "end_time": "10:00"},
    ]
    starts, _ = slots.working_slots(week, MONDAY)
    assert starts == [
        _clock(MONDAY, "09:00"),
        _clock(MONDAY, "09:30"),
        _clock(MONDAY, "17:00"),
        _clock(MONDAY, "17:30"),
    ], starts


def test_each_empty_day_says_why():
    no_schedule = slots.working_slots(None, MONDAY)
    # a day off comes back from Mongo as midnight UTC without a timezone
    day_off = slots.working_slots(_week(blackout_dates=[datetime(2026, 9, 28)]), MONDAY)
    tuesday = slots.working_slots(_week(), MONDAY + timedelta(days=1))

    assert no_schedule == ([], "This doctor has not set their working hours yet")
    assert day_off == ([], "The doctor is not working on this day")
    assert tuesday == ([], "The doctor does not work on this day")


def test_booked_and_past_slots_are_not_free():
    starts, _ = slots.working_slots(_week("09:00", "11:00"), MONDAY)
    booked = [{"scheduled_for": datetime(2026, 9, 28, 4, 30), "duration_minutes": 30}]
    now = _clock(MONDAY, "09:10")

    free = slots.free_slots(starts, booked, 30, now)
    # 09:00 has passed and 09:30 is booked
    assert free == [_clock(MONDAY, "10:00"), _clock(MONDAY, "10:30")], free


def test_a_longer_visit_blocks_every_slot_it_covers():
    starts, _ = slots.working_slots(_week("09:00", "11:00"), MONDAY)
    # booked for an hour, before the doctor moved to 30 minute slots
    booked = [{"scheduled_for": _clock(MONDAY, "09:00"), "duration_minutes": 60}]

    free = slots.free_slots(starts, booked, 30, LONG_AGO)
    assert free == [_clock(MONDAY, "10:00"), _clock(MONDAY, "10:30")], free


# ------------------------------------------------------------ the endpoints


def test_free_slots_leave_out_booked_ones():
    booked = {"_id": ObjectId(), "doctor_id": DOCTOR["_id"], "scheduled_for": SLOT,
              "duration_minutes": 30, "status": "booked"}
    with _FakeDatabase(appointments=[booked]):
        status, body = _reply(slots.get_free_slots(str(DOCTOR["_id"]), DAY))

    assert status == 200, body
    assert body["data"]["date"] == DAY.isoformat()
    assert body["data"]["slot_minutes"] == 30
    assert SLOT.isoformat() not in body["data"]["slots"], body
    assert _clock(DAY, "09:00").isoformat() in body["data"]["slots"], body
    assert body["message"] == "5 free slots", body


def test_a_cancelled_visit_gives_its_slot_back():
    cancelled = {"_id": ObjectId(), "doctor_id": DOCTOR["_id"], "scheduled_for": SLOT,
                 "duration_minutes": 30, "status": "cancelled"}
    with _FakeDatabase(appointments=[cancelled]):
        _, body = _reply(slots.get_free_slots(str(DOCTOR["_id"]), DAY))
    assert SLOT.isoformat() in body["data"]["slots"], body


def test_slots_for_an_unknown_or_inactive_doctor_are_404():
    inactive = {**DOCTOR, "is_active": False}
    with _FakeDatabase(users=[inactive]):
        status, body = _reply(slots.get_free_slots(str(DOCTOR["_id"]), DAY))
        bad_id, _ = _reply(slots.get_free_slots("not-an-id", DAY))
    assert status == 404 and body["error_code"] == "DOCTOR_NOT_FOUND", body
    assert bad_id == 404


def test_the_doctor_list_is_active_doctors_without_their_email():
    retired = {**DOCTOR, "_id": ObjectId(), "full_name": "Dr. Old", "is_active": False}
    with _FakeDatabase(users=[DOCTOR, retired]) as db:
        status, body = _reply(doctors.get_doctors())
    assert status == 200, body
    assert [row["full_name"] for row in body["data"]] == ["Dr. Sara Khan"], body
    assert db.users.queries[0] == {"role": "doctor", "is_active": True}


def test_matching_patients_share_the_requests_number():
    other = {**PATIENT, "_id": ObjectId(), "whatsapp_number": "+923339999999"}
    with _FakeDatabase(patients=[PATIENT, other]):
        status, body = _reply(matching.get_matching_patients(str(REQUEST["_id"])))

    assert status == 200, body
    assert [row["id"] for row in body["data"]] == [str(PATIENT["_id"])], body
    patient = body["data"][0]
    # the birthday alone, and nothing medical
    assert patient["date_of_birth"] == "1998-05-04", patient
    assert "allergies" not in patient and "whatsapp_number" not in patient, patient


def test_a_request_without_a_number_matches_nobody():
    no_number = {**REQUEST, "whatsapp_number": None}
    numberless = {**PATIENT, "whatsapp_number": None}
    with _FakeDatabase(requests=[no_number], patients=[numberless]) as db:
        status, body = _reply(matching.get_matching_patients(str(REQUEST["_id"])))
    assert status == 200 and body["data"] == [], body
    # never asked Mongo for {"whatsapp_number": None}
    assert db.patients.queries == [], db.patients.queries


def test_matching_for_an_unknown_request_is_404():
    with _FakeDatabase(requests=[]):
        status, body = _reply(matching.get_matching_patients(str(ObjectId())))
    assert status == 404 and body["error_code"] == "REQUEST_NOT_FOUND", body


def test_scheduling_a_new_patient_saves_all_three():
    with _FakeDatabase(patients=[]) as db:
        status, body = _schedule()

    assert status == 201, body
    patient = db.patients.inserted[0]
    appointment = db.appointments.inserted[0]
    request = db.booking_requests.docs[0]

    # the patient takes the number the booking came from
    assert patient["full_name"] == "Ayesha Khan"
    assert patient["whatsapp_number"] == "+923001234567"
    assert patient["date_of_birth"] == datetime(1998, 5, 4, tzinfo=UTC)
    assert patient["allergies"] == [] and patient["is_active"] is True

    assert appointment["doctor_id"] == DOCTOR["_id"]
    assert appointment["patient_id"] == patient["_id"]
    assert appointment["scheduled_for"] == SLOT
    assert appointment["duration_minutes"] == 30
    assert appointment["status"] == "booked"
    assert appointment["reason"] == "symptoms"
    assert appointment["symptom_summary"] == "blisters on my feet"
    assert appointment["doctor_snapshot"] == {"full_name": "Dr. Sara Khan"}
    assert appointment["request_id"] == REQUEST["_id"]
    assert appointment["booked_by"] == RECEPTIONIST_ID

    assert request["status"] == "scheduled"
    assert request["patient_id"] == patient["_id"]
    assert request["appointment_id"] == appointment["_id"]
    assert request["handled_by"] == RECEPTIONIST_ID
    assert request["handled_at"] is not None

    assert body["data"]["id"] == str(appointment["_id"])
    assert body["data"]["scheduled_for"] == SLOT.isoformat()


def test_every_write_happens_inside_one_transaction():
    with _FakeDatabase(patients=[]) as db:
        _schedule()
    assert db.transactions == 1
    sessions = (
        db.patients.write_sessions
        + db.appointments.write_sessions
        + db.booking_requests.write_sessions
    )
    # a write without the session would be saved even if the rest failed
    assert len(sessions) == 3 and all(session is SESSION for session in sessions), sessions


def test_scheduling_an_existing_patient_creates_no_new_one():
    with _FakeDatabase() as db:
        status, body = _schedule(patient_id=str(PATIENT["_id"]), new_patient=None)
    assert status == 201, body
    assert db.patients.inserted == []
    assert db.appointments.inserted[0]["patient_id"] == PATIENT["_id"]


def test_a_taken_slot_is_refused_and_nothing_is_written():
    taken = {"_id": ObjectId(), "doctor_id": DOCTOR["_id"], "scheduled_for": SLOT,
             "duration_minutes": 30, "status": "confirmed"}
    with _FakeDatabase(appointments=[taken], patients=[]) as db:
        status, body = _schedule()
    assert status == 409 and body["error_code"] == "SLOT_NOT_FREE", body
    assert db.patients.inserted == [] and len(db.appointments.docs) == 1
    assert db.booking_requests.docs[0]["status"] == "new"


def test_a_time_between_slots_is_refused():
    with _FakeDatabase() as db:
        status, body = _schedule(starts_at=SLOT + timedelta(minutes=10))
    assert status == 409 and body["error_code"] == "SLOT_NOT_FREE", body
    assert db.appointments.inserted == []


def test_a_slot_booked_at_the_same_moment_is_refused():
    # two receptionists passed the slot check together; the index stops one
    appointments = _FakeCollection(insert_error=DuplicateKeyError("E11000 duplicate key"))
    with _FakeDatabase(appointments=(), patients=[PATIENT]) as db:
        db.appointments = appointments
        status, body = _schedule(patient_id=str(PATIENT["_id"]), new_patient=None)
    assert status == 409 and body["error_code"] == "SLOT_NOT_FREE", body


def test_a_handled_request_cannot_be_scheduled_again():
    handled = {**REQUEST, "status": "scheduled"}
    with _FakeDatabase(requests=[handled]) as db:
        status, body = _schedule()
    assert status == 409 and body["error_code"] == "REQUEST_ALREADY_HANDLED", body
    assert db.appointments.inserted == []


def test_unknown_request_doctor_or_patient_is_404():
    with _FakeDatabase(requests=[]):
        request_status, request_body = _schedule()
    with _FakeDatabase(users=[{**DOCTOR, "is_active": False}]):
        doctor_status, doctor_body = _schedule()
    with _FakeDatabase(patients=[]):
        patient_status, patient_body = _schedule(patient_id=str(ObjectId()), new_patient=None)

    assert (request_status, request_body["error_code"]) == (404, "REQUEST_NOT_FOUND")
    assert (doctor_status, doctor_body["error_code"]) == (404, "DOCTOR_NOT_FOUND")
    assert (patient_status, patient_body["error_code"]) == (404, "PATIENT_NOT_FOUND")


def test_a_malformed_id_is_a_400():
    with _FakeDatabase():
        status, body = _schedule(doctor_id="not-an-id")
    assert status == 400 and body["error_code"] == "INVALID_ID", body


def test_a_database_failure_is_a_500_without_details():
    broken = _FakeCollection(error=RuntimeError("connection refused to cluster0"))
    with _FakeDatabase(booking_requests=broken):
        status, body = _schedule()
    assert status == 500, body
    assert "cluster0" not in body["message"], body


def test_declining_marks_the_request_and_who_did_it():
    with _FakeDatabase() as db:
        status, body = _reply(decline.decline_booking_request(str(REQUEST["_id"]), str(RECEPTIONIST_ID)))
    assert status == 200 and body["data"]["status"] == "declined", body
    request = db.booking_requests.docs[0]
    assert request["handled_by"] == RECEPTIONIST_ID and request["handled_at"] is not None


def test_declining_twice_or_an_unknown_request_is_refused():
    handled = {**REQUEST, "status": "scheduled"}
    with _FakeDatabase(requests=[handled]) as db:
        again, again_body = _reply(decline.decline_booking_request(str(REQUEST["_id"]), str(RECEPTIONIST_ID)))
        missing, missing_body = _reply(decline.decline_booking_request(str(ObjectId()), str(RECEPTIONIST_ID)))

    # a scheduled request keeps its appointment
    assert db.booking_requests.docs[0]["status"] == "scheduled"
    assert (again, again_body["error_code"]) == (409, "REQUEST_ALREADY_HANDLED")
    assert (missing, missing_body["error_code"]) == (404, "REQUEST_NOT_FOUND")


# ---------------------------------------------------------- the request body


def _body(**changes):
    return {
        "doctor_id": str(DOCTOR["_id"]),
        "starts_at": "2026-09-24T10:00:00+05:00",
        "new_patient": {"full_name": "  Ayesha Khan  "},
        **changes,
    }


def test_the_body_takes_either_a_patient_or_new_details():
    BookingSchedule.model_validate(_body())
    BookingSchedule.model_validate(_body(new_patient=None, patient_id=str(PATIENT["_id"])))

    for wrong in (_body(patient_id=str(PATIENT["_id"])), _body(new_patient=None)):
        try:
            BookingSchedule.model_validate(wrong)
        except ValidationError:
            continue
        raise AssertionError(f"accepted {wrong}")


def test_the_time_must_say_its_timezone():
    try:
        BookingSchedule.model_validate(_body(starts_at="2026-09-24T10:00:00"))
    except ValidationError:
        return
    raise AssertionError("accepted a time without a timezone")


def test_new_patient_details_are_checked():
    booking = BookingSchedule.model_validate(_body())
    assert booking.new_patient.full_name == "Ayesha Khan"

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    for wrong in ({"full_name": "A"}, {"full_name": "Ayesha", "date_of_birth": tomorrow},
                  {"full_name": "Ayesha", "gender": "unknown"}):
        try:
            BookingSchedule.model_validate(_body(new_patient=wrong))
        except ValidationError:
            continue
        raise AssertionError(f"accepted {wrong}")


def test_every_scheduling_route_needs_a_signed_in_receptionist():
    request_id = str(REQUEST["_id"])
    responses = [
        client.get("/receptionist/doctors"),
        client.get(f"/receptionist/doctors/{DOCTOR['_id']}/slots", params={"date": "2026-09-24"}),
        client.get(f"/receptionist/booking-requests/{request_id}/patients"),
        client.post(f"/receptionist/booking-requests/{request_id}/schedule", json=_body()),
        client.patch(f"/receptionist/booking-requests/{request_id}/decline"),
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
