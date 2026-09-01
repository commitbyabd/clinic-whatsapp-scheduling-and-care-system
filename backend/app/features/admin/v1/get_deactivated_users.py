from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_deactivated_users():
    try:
        # Staff only: a deactivated admin is not something this screen manages
        cursor = get_database().users.find(
            {"is_active": False},
            {
                "_id": 1,
                "full_name": 1,
                "email": 1,
                "role": 1,
                "specialization": 1,
            },
        )
        deactivated_users = await cursor.to_list(length=None)

        return api_response(
            status_code=200,
            message="Deactivated users retrieved successfully",
            data=serialize_data(deactivated_users),
        )
    except Exception:
        logger.exception("Error in get_deactivated_users")

        return api_response(
            status_code=500,
            message="An error occurred while retrieving deactivated users",
            error_code="DEACTIVATED_USERS_FAILED",
            data=None,
        )
