from datetime import datetime, time, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

from .get_appointments import shape_consultation

# A visit that is still ahead or already done. A cancelled or missed visit
# never happened, so it has nothing to write up.
CONSULTABLE = ["booked", "confirmed", "completed"]


async def save_consultation(payload: dict):
    doctor_id = payload.get("doctor_id")
    appointment_id = payload.get("appointment_id")

    # doctor_id comes off the token and appointment_id off the URL, so only
    # the second one can be anything the client felt like typing
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
        appointment = await save_consultation_query(
            doctor_id,
            appointment_id,
            consultation_document(payload),
            payload.get("doctor_notes") or "",
        )

        if appointment is None:
            # This doctor's visit, but cancelled or missed. Another doctor's
            # visit answers 404 like a missing one, so it is never confirmed
            # to exist.
            if await own_appointment_exists_query(doctor_id, appointment_id):
                return api_response(
                    status_code=409,
                    message="A cancelled or missed visit has no consultation",
                    error_code="CONSULTATION_NOT_ALLOWED",
                    data=None,
                )

            return api_response(
                status_code=404,
                message="Appointment not found",
                error_code="APPOINTMENT_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Consultation saved",
            data=serialize_data(
                {
                    "_id": appointment["_id"],
                    "consultation": shape_consultation(appointment.get("consultation")),
                    "doctor_notes": appointment.get("doctor_notes", ""),
                    "notes_updated_at": appointment.get("notes_updated_at"),
                }
            ),
        )

    except Exception:
        logger.exception("Error in save_consultation")

        return api_response(
            status_code=500,
            message="Could not save the consultation",
            error_code="CONSULTATION_SAVE_FAILED",
            data=None,
        )


def consultation_document(payload: dict) -> dict:
    follow_up = payload.get("follow_up_on")

    return {
        "diagnosis": payload.get("diagnosis") or "",
        "vitals": payload.get("vitals") or {},
        "prescriptions": payload.get("prescriptions") or [],
        # BSON has no plain date, so midnight UTC stands for the day
        "follow_up_on": (
            datetime.combine(follow_up, time.min, tzinfo=timezone.utc)
            if follow_up
            else None
        ),
    }


async def save_consultation_query(
    doctor_id: str, appointment_id: str, consultation: dict, doctor_notes: str
) -> dict | None:
    now = datetime.now(timezone.utc)

    # doctor_id in the filter is the security boundary: without it any doctor
    # could write into any other doctor's consultation by guessing an id
    return await get_database().appointments.find_one_and_update(
        {
            "_id": ObjectId(appointment_id),
            "doctor_id": ObjectId(doctor_id),
            "status": {"$in": CONSULTABLE},
        },
        {
            # replaced whole: the form sends every field each time
            "$set": {
                "consultation": consultation,
                "doctor_notes": doctor_notes,
                # kept apart from updated_at, so a status change later does
                # not look like the clinical record was touched
                "notes_updated_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def own_appointment_exists_query(doctor_id: str, appointment_id: str) -> bool:
    row = await get_database().appointments.find_one(
        {"_id": ObjectId(appointment_id), "doctor_id": ObjectId(doctor_id)},
        {"_id": 1},
    )
    return row is not None
