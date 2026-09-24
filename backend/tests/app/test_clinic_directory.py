"""
Tests for the doctors the chatbot reads out of MongoDB: who it offers, and
which of their slots are still open.

A small blocking fake stands in for pymongo (the chat reads with the plain
client, not the async one), so these need no database.

    python tests/app/test_clinic_directory.py
    pytest
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bson import ObjectId  # noqa: E402

from app.core.clinic_time import CLINIC_TZ  # noqa: E402
from app.features.whatsapp.v1.clinic_directory import MongoDirectory  # noqa: E402
from fake_mongo import matches  # noqa: E402

ALI, SARA, HINA = ObjectId(), ObjectId(), ObjectId()

# every day, so there is always a next open time however this test is run
ALL_WEEK = [
    {"day_of_week": day, "start_time": start, "end_time": end}
    for day in range(7)
    for start, end in (("09:00", "13:00"), ("17:00", "20:00"))
]


def _doctor(_id, name, specialization="General Physician", **changes):
    return {
        "_id": _id,
        "full_name": name,
        "specialization": specialization,
        "role": "doctor",
        "is_active": True,
        **changes,
    }


def _schedule(doctor_id, **changes):
    return {
        "doctor_id": doctor_id,
        "is_active": True,
        "slot_minutes": 30,
        "working_hours": ALL_WEEK,
        **changes,
    }


class _Cursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, key, direction):
        self.rows.sort(key=lambda row: row.get(key), reverse=direction == -1)
        return self

    def __iter__(self):
        return iter(self.rows)


class _Collection:
    def __init__(self, docs=()):
        self.docs = [dict(doc) for doc in docs]

    def find(self, query, projection=None):
        return _Cursor([dict(doc) for doc in self.docs if matches(doc, query)])

    def find_one(self, query, projection=None):
        return next((dict(doc) for doc in self.docs if matches(doc, query)), None)


class _Db:
    def __init__(self, users=(), schedules=(), appointments=()):
        self.users = _Collection(users)
        self.schedules = _Collection(schedules)
        self.appointments = _Collection(appointments)


def _clinic() -> MongoDirectory:
    """Two general physicians, one of them walk-in, and a dermatologist."""
    return MongoDirectory(
        _Db(
            users=[
                _doctor(ALI, "Dr. Ali Raza"),
                _doctor(SARA, "Dr. Sara Malik", booking_mode="walk_in"),
                _doctor(HINA, "Dr. Hina Shah", "Dermatologist"),
            ],
            schedules=[_schedule(ALI), _schedule(SARA), _schedule(HINA)],
        )
    )


# --- who is offered ------------------------------------------------------


def test_doctors_come_back_in_name_order():
    names = [doctor.name for doctor in _clinic().doctors()]
    assert names == ["Dr. Ali Raza", "Dr. Hina Shah", "Dr. Sara Malik"], names


def test_a_department_narrows_the_list():
    doctors = _clinic().doctors("Dermatologist")
    assert [doctor.name for doctor in doctors] == ["Dr. Hina Shah"]
    assert _clinic().doctors("Neurologist") == []


def test_the_booking_mode_says_who_is_walk_in():
    doctors = {doctor.name: doctor for doctor in _clinic().doctors()}
    # not set means by appointment, so existing doctors keep working
    assert doctors["Dr. Ali Raza"].walk_in is False
    assert doctors["Dr. Sara Malik"].walk_in is True


def test_a_doctor_who_cannot_be_seen_is_not_offered():
    clinic = MongoDirectory(
        _Db(
            users=[
                _doctor(ALI, "Dr. Ali Raza", is_active=False),
                _doctor(SARA, "Dr. Sara Malik"),  # no hours set yet
                _doctor(HINA, "Dr. Hina Shah", "Dermatologist"),
            ],
            schedules=[_schedule(ALI), _schedule(HINA, is_active=False)],
        )
    )
    assert clinic.doctors() == []
    assert clinic.doctor(str(SARA)) is None


def test_one_doctor_is_read_by_id():
    doctor = _clinic().doctor(str(HINA))
    assert doctor.name == "Dr. Hina Shah"
    assert doctor.specialization == "Dermatologist"
    # (day, start, end), sorted, as the chat describes them
    assert doctor.hours[0] == (0, "09:00", "13:00")
    assert _clinic().doctor("not-an-id") is None
    assert _clinic().doctor(str(ObjectId())) is None


# --- open times ----------------------------------------------------------


def test_open_times_are_future_clinic_times_in_order():
    times = _clinic().open_times(str(ALI), 4)

    assert len(times) == 4
    assert times == sorted(times)
    assert times[0] > datetime.now(CLINIC_TZ), "an open time cannot be in the past"
    for moment in times:
        assert moment.utcoffset() == timedelta(hours=5), moment
        assert moment.minute in (0, 30) and moment.hour in range(9, 20), moment


def test_a_booked_slot_is_not_offered():
    clinic = _clinic()
    first, second, _ = clinic.open_times(str(ALI), 3)

    # Mongo hands times back without a timezone, so store it the same way
    clinic.db.appointments.docs.append(
        {
            "doctor_id": ALI,
            "status": "booked",
            "scheduled_for": first.astimezone(timezone.utc).replace(tzinfo=None),
            "duration_minutes": 30,
        }
    )

    assert clinic.open_times(str(ALI), 3)[0] == second
    # another doctor's day is untouched
    assert clinic.open_times(str(SARA), 3)[0] == first


def test_a_cancelled_visit_gives_its_slot_back():
    clinic = _clinic()
    first = clinic.open_times(str(ALI), 1)[0]
    clinic.db.appointments.docs.append(
        {
            "doctor_id": ALI,
            "status": "cancelled",
            "scheduled_for": first.astimezone(timezone.utc).replace(tzinfo=None),
            "duration_minutes": 30,
        }
    )
    assert clinic.open_times(str(ALI), 1)[0] == first


def test_a_doctor_without_hours_has_no_open_times():
    clinic = MongoDirectory(_Db(users=[_doctor(ALI, "Dr. Ali Raza")]))
    assert clinic.open_times(str(ALI), 6) == []


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
