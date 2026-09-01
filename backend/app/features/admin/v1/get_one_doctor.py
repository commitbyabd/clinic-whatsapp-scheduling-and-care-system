from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_one_doctor(doctor_id: str):
    try:
        # malformed id, treat the same as "not found"
        if not ObjectId.is_valid(doctor_id):
            return api_response(
                status_code=404,
                message="Doctor not found",
                error_code="DOCTOR_NOT_FOUND",
                data=None,
            )

        doctor = await get_database().users.find_one(
            {"_id": ObjectId(doctor_id), "role": "doctor"},
            {
                "_id": 1,
                "full_name": 1,
                "email": 1,
                "specialization": 1,
                "is_active": 1,
            },
        )

        # the id is valid but no doctor exists against it
        if doctor is None:
            return api_response(
                status_code=404,
                message="Doctor not found",
                error_code="DOCTOR_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Doctor retrieved successfully",
            data=serialize_data(doctor),
        )

    except Exception:
        logger.exception("Error in get_one_doctor")

        return api_response(
            status_code=500,
            message="Could not retrieve the doctor",
            error_code="DOCTOR_FETCH_FAILED",
            data=None,
        )
