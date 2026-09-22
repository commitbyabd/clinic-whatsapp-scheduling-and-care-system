from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.clinic_time import CLINIC_TZ
from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

from .get_free_slots import (
    ACTIVE_STATUSES,
    booked_query,
    find_doctor_query,
    find_schedule_query,
    free_slots,
    slot_minutes,
    working_slots,
)
from .schedule_booking_request import SLOT_GONE


async def reschedule_appointment(payload: dict):
    appointment_id = payload.get("appointment_id")
    doctor_id = payload.get("doctor_id")
    receptionist_id = payload.get("receptionist_id")

    ids = [appointment_id, doctor_id, receptionist_id]
    if not all(isinstance(value, str) and ObjectId.is_valid(value) for value in ids):
        return api_response(
            status_code=400,
            message="An ID in this change is not valid",
            error_code="INVALID_ID",
            data=None,
        )

    try:
        appointment = await find_appointment_query(appointment_id)
        if appointment is None:
            return api_response(
                status_code=404,
                message="Appointment not found",
                error_code="APPOINTMENT_NOT_FOUND",
                data=None,
            )
        if appointment.get("status") not in ACTIVE_STATUSES:
            return api_response(
                status_code=409,
                message="Only a visit that is still to come can be moved",
                error_code="APPOINTMENT_NOT_MOVABLE",
                data=None,
            )

        doctor = await find_doctor_query(doctor_id)
        if doctor is None:
            return api_response(
                status_code=404,
                message="Doctor not found",
                error_code="DOCTOR_NOT_FOUND",
                data=None,
            )

        starts_at = payload["starts_at"].astimezone(timezone.utc)
        schedule = await find_schedule_query(doctor_id)
        day = starts_at.astimezone(CLINIC_TZ).date()
        starts, _ = working_slots(schedule, day)
        minutes = slot_minutes(schedule)

        # The visit being moved must not block its own new time: moving an
        # hour-long visit half an hour later overlaps where it is now.
        booked = [
            row
            for row in await booked_query(doctor_id, day)
            if row["_id"] != appointment["_id"]
        ]

        if starts_at not in free_slots(starts, booked, minutes, datetime.now(timezone.utc)):
            return api_response(
                status_code=409,
                message=SLOT_GONE,
                error_code="SLOT_NOT_FREE",
                data=None,
            )

        row = await reschedule_appointment_query(
            appointment, doctor, starts_at, minutes, receptionist_id
        )

        if row is None:
            return api_response(
                status_code=409,
                message="This visit changed a moment ago. Reload and try again.",
                error_code="APPOINTMENT_CHANGED",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Appointment moved",
            data=serialize_data(
                {
                    "_id": row["_id"],
                    "doctor_id": row["doctor_id"],
                    "scheduled_for": row["scheduled_for"],
                    "duration_minutes": row["duration_minutes"],
                    "status": row["status"],
                }
            ),
        )

    except DuplicateKeyError:
        # the unique slot index caught another booking at the same moment
        return api_response(
            status_code=409,
            message=SLOT_GONE,
            error_code="SLOT_NOT_FREE",
            data=None,
        )

    except Exception:
        logger.exception("Error in reschedule_appointment")

        return api_response(
            status_code=500,
            message="Could not move the appointment",
            error_code="RESCHEDULE_FAILED",
            data=None,
        )


async def find_appointment_query(appointment_id: str) -> dict | None:
    return await get_database().appointments.find_one({"_id": ObjectId(appointment_id)})


async def reschedule_appointment_query(
    appointment: dict,
    doctor: dict,
    starts_at: datetime,
    minutes: int,
    receptionist_id: str,
) -> dict | None:
    now = datetime.now(timezone.utc)

    return await get_database().appointments.find_one_and_update(
        # the status read a moment ago, so a cancel made in between wins
        {"_id": appointment["_id"], "status": appointment["status"]},
        {
            "$set": {
                "doctor_id": doctor["_id"],
                "doctor_snapshot": {"full_name": doctor.get("full_name")},
                "specialization": doctor.get("specialization"),
                "scheduled_for": starts_at,
                "duration_minutes": minutes,
                # a new time the patient has not agreed to yet
                "status": "booked",
                "rescheduled_by": ObjectId(receptionist_id),
                "rescheduled_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
