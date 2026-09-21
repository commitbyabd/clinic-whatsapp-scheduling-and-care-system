from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def decline_booking_request(request_id: str, receptionist_id: str):
    try:
        if not ObjectId.is_valid(request_id) or not ObjectId.is_valid(receptionist_id):
            return api_response(
                status_code=400,
                message="Booking request ID is not valid",
                error_code="INVALID_REQUEST_ID",
                data=None,
            )

        row = await decline_booking_request_query(request_id, receptionist_id)

        # nothing changed: either there is no such request, or it has
        # already been scheduled or declined
        if row is None:
            if await request_exists_query(request_id):
                return api_response(
                    status_code=409,
                    message="This request has already been handled",
                    error_code="REQUEST_ALREADY_HANDLED",
                    data=None,
                )

            return api_response(
                status_code=404,
                message="Booking request not found",
                error_code="REQUEST_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Request declined",
            data=serialize_data({"_id": row["_id"], "status": row["status"]}),
        )

    except Exception:
        logger.exception("Error in decline_booking_request")

        return api_response(
            status_code=500,
            message="Could not decline the request",
            error_code="DECLINE_FAILED",
            data=None,
        )


async def decline_booking_request_query(request_id: str, receptionist_id: str) -> dict | None:
    # only a new request can be declined, so a scheduled one keeps its
    # appointment
    return await get_database().booking_requests.find_one_and_update(
        {"_id": ObjectId(request_id), "status": "new"},
        {
            "$set": {
                "status": "declined",
                "handled_by": ObjectId(receptionist_id),
                "handled_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def request_exists_query(request_id: str) -> bool:
    row = await get_database().booking_requests.find_one(
        {"_id": ObjectId(request_id)}, {"_id": 1}
    )
    return row is not None
