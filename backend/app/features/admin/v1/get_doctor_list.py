from app.core.response import api_response
from app.core.database import get_database
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_doctor_list():
    try:
        cursor = get_database().users.find(
            {"role": "doctor", "is_active": True},
            {"_id": 1, "full_name": 1, "email": 1, "specialization": 1},
        )
        doctors = await cursor.to_list(length=None)
        doctors = serialize_data(doctors)

        return api_response(
            status_code=200,
            message="Doctors list retrieved successfully",
            data=doctors,
        )

    except Exception:
        logger.exception("Error in get_doctor_list")

        return api_response(
            status_code=500,
            message="Could not retrieve the doctor list",
            error_code="DOCTOR_LIST_FAILED",
            data=None,
        )
