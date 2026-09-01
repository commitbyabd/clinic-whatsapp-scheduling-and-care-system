from datetime import datetime, time, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def edit_doctor_schedule(payload: dict):
    doctor_id = payload.get("doctor_id")
    working_hours = payload.get("working_hours")
    slot_minutes = payload.get("slot_minutes")
    blackout_dates = payload.get("blackout_dates")

    try:
        if not isinstance(doctor_id, str) or not ObjectId.is_valid(doctor_id):
            return api_response(
                status_code=400,
                message="Doctor ID is not valid",
                error_code="INVALID_DOCTOR_ID",
                data=None,
            )

        # The schema hands back datetime.date, which BSON cannot encode at all.
        # Midnight UTC is the storable equivalent of "this whole day is off".
        blackouts = [
            datetime.combine(day, time.min, tzinfo=timezone.utc)
            for day in (blackout_dates or [])
        ]

        schedule = await edit_doctor_schedule_query(
            doctor_id,
            {
                "working_hours": working_hours or [],
                "slot_minutes": slot_minutes,
                "blackout_dates": blackouts,
                # editing a retired schedule is how a doctor comes back
                "is_active": True,
            },
        )

        return api_response(
            status_code=200,
            message="Schedule saved successfully",
            data=serialize_data(schedule),
        )

    except Exception:
        logger.exception("Error in edit_doctor_schedule")

        return api_response(
            status_code=500,
            message="Could not save the schedule",
            error_code="SCHEDULE_SAVE_FAILED",
            data=None,
        )


async def edit_doctor_schedule_query(doctor_id: str, fields: dict) -> dict:
    now = datetime.now(timezone.utc)

    # The whole week arrives at once, so this replaces rather than merges: a day
    # the doctor removed from the table has to disappear from the document too.
    #
    # Matched on doctor_id alone. Adding is_active here would miss a retired
    # schedule and insert a second document for the same doctor.
    return await get_database().schedules.find_one_and_update(
        {"doctor_id": ObjectId(doctor_id)},
        {
            "$set": {**fields, "updated_at": now},
            # doctor_id is not repeated here: an upsert already takes the
            # equality fields of the filter across to the new document.
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,  # a doctor setting hours for the first time has no document
        return_document=ReturnDocument.AFTER,
    )
