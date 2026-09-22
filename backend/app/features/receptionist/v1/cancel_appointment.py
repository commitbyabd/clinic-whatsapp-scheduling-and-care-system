from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

from .get_free_slots import ACTIVE_STATUSES


async def cancel_appointment(appointment_id: str, receptionist_id: str, reason: str | None):
    if not ObjectId.is_valid(appointment_id) or not ObjectId.is_valid(receptionist_id):
        return api_response(
            status_code=400,
            message="Appointment ID is not valid",
            error_code="INVALID_APPOINTMENT_ID",
            data=None,
        )

    try:
        row = await cancel_appointment_query(appointment_id, receptionist_id, reason)

        if row is None:
            if await appointment_exists_query(appointment_id):
                return api_response(
                    status_code=409,
                    message="Only a visit that is still to come can be cancelled",
                    error_code="APPOINTMENT_NOT_CANCELLABLE",
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
            message="Appointment cancelled",
            data=serialize_data({"_id": row["_id"], "status": row["status"]}),
        )

    except Exception:
        logger.exception("Error in cancel_appointment")

        return api_response(
            status_code=500,
            message="Could not cancel the appointment",
            error_code="CANCEL_FAILED",
            data=None,
        )


async def cancel_appointment_query(
    appointment_id: str, receptionist_id: str, reason: str | None
) -> dict | None:
    now = datetime.now(timezone.utc)

    # Kept, never deleted: a cancelled visit stays on the record, and the
    # unique slot index ignores it, so the time is free to book again.
    return await get_database().appointments.find_one_and_update(
        {"_id": ObjectId(appointment_id), "status": {"$in": ACTIVE_STATUSES}},
        {
            "$set": {
                "status": "cancelled",
                "cancel_reason": reason or None,
                "cancelled_by": ObjectId(receptionist_id),
                "cancelled_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def appointment_exists_query(appointment_id: str) -> bool:
    row = await get_database().appointments.find_one(
        {"_id": ObjectId(appointment_id)}, {"_id": 1}
    )
    return row is not None
