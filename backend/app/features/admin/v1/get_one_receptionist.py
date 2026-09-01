from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_one_receptionist(receptionist_id: str):
    try:
        # malformed id, treat the same as "not found"
        if not ObjectId.is_valid(receptionist_id):
            return api_response(
                status_code=404,
                message="Receptionist not found",
                error_code="RECEPTIONIST_NOT_FOUND",
                data=None,
            )

        receptionist = await get_database().users.find_one(
            {"_id": ObjectId(receptionist_id), "role": "receptionist"},
            {
                "_id": 1,
                "full_name": 1,
                "email": 1,
                "is_active": 1,
            },
        )

        # the id is valid but no receptionist exists against it
        if receptionist is None:
            return api_response(
                status_code=404,
                message="Receptionist not found",
                error_code="RECEPTIONIST_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Receptionist retrieved successfully",
            data=serialize_data(receptionist),
        )

    except Exception:
        logger.exception("Error in get_one_receptionist")

        return api_response(
            status_code=500,
            message="Could not retrieve the receptionist",
            error_code="RECEPTIONIST_FETCH_FAILED",
            data=None,
        )
