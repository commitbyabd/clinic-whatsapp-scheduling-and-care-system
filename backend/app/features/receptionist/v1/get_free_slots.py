from datetime import date, datetime, timezone

from bson import ObjectId

from app.core.clinic_time import clinic_day_bounds
from app.core.database import get_database
from app.core.response import api_response

# The slot maths now lives in app/core/slots.py, shared with the WhatsApp
# chat. Re-exported here because booking and moving a visit import it from
# this module.
from app.core.slots import (  # noqa: F401
    ACTIVE_STATUSES,
    DEFAULT_SLOT_MINUTES,
    free_slots,
    slot_minutes,
    working_slots,
)
from app.utils.object_serializer import serialize_data
from logging_config import logger


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
