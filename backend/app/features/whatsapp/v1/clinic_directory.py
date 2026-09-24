"""The doctors, their weekly hours and open times, read from MongoDB for
the chatbot (chatbot/directory.py describes what it needs)."""

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.core.clinic_time import CLINIC_TZ, clinic_day_bounds
from app.core.slots import ACTIVE_STATUSES, free_slots, slot_minutes, working_slots
from chatbot.directory import Doctor

# How far ahead open times are looked for. The chat tells the patient "the
# next two weeks" when there are none, so the two change together.
SEARCH_DAYS = 14

DOCTOR_FIELDS = {"full_name": 1, "specialization": 1, "booking_mode": 1}


class MongoDirectory:
    """Reads for the booking chat. handle_message runs on a worker thread,
    so this takes a plain blocking database, like MongoStateStore."""

    def __init__(self, db):
        self.db = db

    def doctors(self, specialization: str | None = None) -> list[Doctor]:
        # active doctors with hours set: one without hours cannot be seen
        query = {"role": "doctor", "is_active": True}
        if specialization:
            query["specialization"] = specialization

        users = list(self.db.users.find(query, DOCTOR_FIELDS).sort("full_name", 1))
        schedules = self._schedules([user["_id"] for user in users])
        doctors = [_doctor(user, schedules.get(user["_id"])) for user in users]
        return [doctor for doctor in doctors if doctor.hours]

    def doctor(self, doctor_id: str) -> Doctor | None:
        if not ObjectId.is_valid(doctor_id):
            return None
        user = self.db.users.find_one(
            {"_id": ObjectId(doctor_id), "role": "doctor", "is_active": True},
            DOCTOR_FIELDS,
        )
        if user is None:
            return None
        doctor = _doctor(user, self._schedules([user["_id"]]).get(user["_id"]))
        return doctor if doctor.hours else None

    def open_times(self, doctor_id: str, limit: int) -> list[datetime]:
        """The next free slots from now, soonest first, in clinic time. The
        same maths reception books with, so the chat never offers a time
        the desk could not."""
        schedule = self.db.schedules.find_one(
            {"doctor_id": ObjectId(doctor_id), "is_active": True}
        )
        if not schedule:
            return []

        today = datetime.now(CLINIC_TZ).date()
        window_start, _ = clinic_day_bounds(today)
        _, window_end = clinic_day_bounds(today + timedelta(days=SEARCH_DAYS - 1))

        # one read for the whole window rather than one per day
        booked = list(
            self.db.appointments.find(
                {
                    "doctor_id": ObjectId(doctor_id),
                    "status": {"$in": ACTIVE_STATUSES},
                    "scheduled_for": {"$gte": window_start, "$lt": window_end},
                },
                {"scheduled_for": 1, "duration_minutes": 1},
            )
        )

        now = datetime.now(timezone.utc)
        minutes = slot_minutes(schedule)
        found: list[datetime] = []

        for offset in range(SEARCH_DAYS):
            starts, _ = working_slots(schedule, today + timedelta(days=offset))
            for start in free_slots(starts, booked, minutes, now):
                found.append(start.astimezone(CLINIC_TZ))
                if len(found) >= limit:
                    return found
        return found

    def _schedules(self, doctor_ids: list) -> dict:
        if not doctor_ids:
            return {}
        rows = self.db.schedules.find(
            {"doctor_id": {"$in": doctor_ids}, "is_active": True}
        )
        return {row["doctor_id"]: row for row in rows}


def _doctor(user: dict, schedule: dict | None) -> Doctor:
    blocks = (schedule or {}).get("working_hours") or []
    return Doctor(
        id=str(user["_id"]),
        name=user.get("full_name") or "Our doctor",
        specialization=user.get("specialization") or "Doctor",
        walk_in=user.get("booking_mode") == "walk_in",
        hours=tuple(
            sorted(
                (block["day_of_week"], block["start_time"], block["end_time"])
                for block in blocks
            )
        ),
    )
