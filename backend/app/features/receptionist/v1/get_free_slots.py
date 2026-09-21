from datetime import date, datetime, timedelta, timezone

from bson import ObjectId

from app.core.clinic_time import as_utc, clinic_day_bounds, clinic_time
from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

# the schedule schema's default, for a schedule saved without one
DEFAULT_SLOT_MINUTES = 30

# The statuses that hold a slot. A cancelled visit gives its slot back, and
# completed and no_show visits are already in the past.
ACTIVE_STATUSES = ["booked", "confirmed"]


async def get_free_slots(doctor_id: str, day: date):
    try:
        if not ObjectId.is_valid(doctor_id) or await find_doctor_query(doctor_id) is None:
            return api_response(
                status_code=404,
                message="Doctor not found",
                error_code="DOCTOR_NOT_FOUND",
                data=None,
            )

        schedule = await find_schedule_query(doctor_id)
        starts, closed = working_slots(schedule, day)
        booked = await booked_query(doctor_id, day) if starts else []
        minutes = slot_minutes(schedule)
        free = free_slots(starts, booked, minutes, datetime.now(timezone.utc))

        if closed:
            message = closed
        elif free:
            message = f"{len(free)} free slot{'' if len(free) == 1 else 's'}"
        else:
            message = "No free slots left on this day"

        return api_response(
            status_code=200,
            message=message,
            data=serialize_data({"date": day, "slot_minutes": minutes, "slots": free}),
        )

    except Exception:
        logger.exception("Error in get_free_slots")

        return api_response(
            status_code=500,
            message="Could not work out the free slots",
            error_code="SLOTS_FETCH_FAILED",
            data=None,
        )


def slot_minutes(schedule: dict | None) -> int:
    return (schedule or {}).get("slot_minutes") or DEFAULT_SLOT_MINUTES


def working_slots(
    schedule: dict | None, day: date
) -> tuple[list[datetime], str | None]:
    """Every slot start the doctor works on a clinic day, in UTC.

    When there are none, the second value says why, for the receptionist.
    """
    if not schedule:
        return [], "This doctor has not set their working hours yet"

    # a day off is stored as midnight UTC of that day
    days_off = {as_utc(day_off).date() for day_off in schedule.get("blackout_dates") or []}
    if day in days_off:
        return [], "The doctor is not working on this day"

    step = timedelta(minutes=slot_minutes(schedule))
    starts = []

    for block in schedule.get("working_hours") or []:
        # 0 is Monday in the schedule and in Python alike
        if block.get("day_of_week") != day.weekday():
            continue

        start = clinic_time(day, block["start_time"])
        end = clinic_time(day, block["end_time"])

        # a slot has to finish by the end of its block
        while start + step <= end:
            starts.append(start.astimezone(timezone.utc))
            start += step

    if not starts:
        return [], "The doctor does not work on this day"

    return sorted(starts), None


def free_slots(
    starts: list[datetime], booked: list[dict], minutes: int, now: datetime
) -> list[datetime]:
    """The starts still open: not in the past, and not overlapping a booking."""
    step = timedelta(minutes=minutes)

    taken = [
        (
            as_utc(row["scheduled_for"]),
            timedelta(minutes=row.get("duration_minutes") or minutes),
        )
        for row in booked
    ]

    # Overlap rather than equal start times, so a visit booked before the
    # doctor changed their slot length still blocks every slot it covers.
    return [
        start
        for start in starts
        if start > now
        and not any(
            begins < start + step and start < begins + length
            for begins, length in taken
        )
    ]


async def find_doctor_query(doctor_id: str, session=None) -> dict | None:
    return await get_database().users.find_one(
        {"_id": ObjectId(doctor_id), "role": "doctor", "is_active": True},
        {"full_name": 1, "specialization": 1},
        session=session,
    )


async def find_schedule_query(doctor_id: str, session=None) -> dict | None:
    return await get_database().schedules.find_one(
        {"doctor_id": ObjectId(doctor_id), "is_active": True},
        session=session,
    )


async def booked_query(doctor_id: str, day: date, session=None) -> list[dict]:
    day_start, day_end = clinic_day_bounds(day)

    cursor = get_database().appointments.find(
        {
            "doctor_id": ObjectId(doctor_id),
            "status": {"$in": ACTIVE_STATUSES},
            "scheduled_for": {"$gte": day_start, "$lt": day_end},
        },
        {"scheduled_for": 1, "duration_minutes": 1},
        session=session,
    )
    return await cursor.to_list(length=None)
