from app.core.response import api_response
from app.core.database import get_database
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_receptionist_list():
    try:
        cursor = get_database().users.find(
            {"role": "receptionist", "is_active": True},
            {"_id": 1, "full_name": 1, "email": 1},
        )
        receptionists = await cursor.to_list(length=None)
        receptionists = serialize_data(receptionists)

        return api_response(
            status_code=200,
            message="Receptionists list retrieved successfully",
            data=receptionists,
        )

    except Exception:
        logger.exception("Error in get_receptionist_list")

        return api_response(
            status_code=500,
            message="Could not retrieve the receptionist list",
            error_code="RECEPTIONIST_LIST_FAILED",
            data=None,
        )
