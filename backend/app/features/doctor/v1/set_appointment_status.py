from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.clinic_time import CLINIC_TZ, as_utc, clinic_day_bounds
from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

DONE_MESSAGES = {
    "booked": "Visit reopened",
    "completed": "Visit marked as completed",
    "no_show": "Visit marked as a no-show",
}


async def set_appointment_status(payload: dict):
    doctor_id = payload.get("doctor_id")
    appointment_id = payload.get("appointment_id")
    status = payload.get("status")

    if not isinstance(appointment_id, str) or not ObjectId.is_valid(appointment_id):
        return api_response(
            status_code=400,
            message="Appointment ID is not valid",
            error_code="INVALID_APPOINTMENT_ID",
            data=None,
        )

    if not isinstance(doctor_id, str) or not ObjectId.is_valid(doctor_id):
        return api_response(
            status_code=400,
            message="Doctor ID is not valid",
            error_code="INVALID_DOCTOR_ID",
            data=None,
        )

    try:
        appointment = await find_own_appointment_query(doctor_id, appointment_id)

        # missing, or another doctor's: the same answer either way
        if appointment is None:
            return api_response(
                status_code=404,
                message="Appointment not found",
                error_code="APPOINTMENT_NOT_FOUND",
                data=None,
            )

        if appointment.get("status") == "cancelled":
            return api_response(
                status_code=409,
                message="A cancelled visit cannot be changed",
                error_code="APPOINTMENT_CANCELLED",
                data=None,
            )

        # a visit on a later day cannot have happened, or been missed, yet
        if status in ("completed", "no_show") and not is_today_or_earlier(
            appointment["scheduled_for"]
        ):
            return api_response(
                status_code=409,
                message="This visit is on a later day, so it cannot be marked yet",
                error_code="VISIT_NOT_YET",
                data=None,
            )

        row = await set_appointment_status_query(
            doctor_id, appointment_id, appointment.get("status"), status
        )

        if row is None:
            return api_response(
                status_code=409,
                message="This visit changed a moment ago. Reload and try again.",
                error_code="STATUS_CHANGED",
                data=None,
            )

        return api_response(
            status_code=200,
            message=DONE_MESSAGES[status],
            data=serialize_data({"_id": row["_id"], "status": row["status"]}),
        )

    except DuplicateKeyError:
        # Reopening puts the visit back in its slot, which another booking
        # may hold now that this one was completed or missed.
        return api_response(
            status_code=409,
            message="Another visit has been booked in this slot since, so this one cannot be reopened",
            error_code="SLOT_TAKEN",
            data=None,
        )

    except Exception:
        logger.exception("Error in set_appointment_status")

        return api_response(
            status_code=500,
            message="Could not change the visit",
            error_code="STATUS_SAVE_FAILED",
            data=None,
        )


def is_today_or_earlier(scheduled_for: datetime) -> bool:
    _, end_of_today = clinic_day_bounds(datetime.now(CLINIC_TZ).date())
    return as_utc(scheduled_for) < end_of_today


async def find_own_appointment_query(doctor_id: str, appointment_id: str) -> dict | None:
    return await get_database().appointments.find_one(
        {"_id": ObjectId(appointment_id), "doctor_id": ObjectId(doctor_id)},
        {"status": 1, "scheduled_for": 1},
    )


async def set_appointment_status_query(
    doctor_id: str, appointment_id: str, current: str, status: str
) -> dict | None:
    # the status read a moment ago goes in the filter, so a change made in
    # between is never overwritten
    return await get_database().appointments.find_one_and_update(
        {
            "_id": ObjectId(appointment_id),
            "doctor_id": ObjectId(doctor_id),
            "status": current,
        },
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
