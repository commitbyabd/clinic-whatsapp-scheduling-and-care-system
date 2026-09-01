from bson import ObjectId
from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_doctor_schedule(doctor_id: str):
    try:
        # the id is read off the signed token, so a bad one means corrupt data
        if not ObjectId.is_valid(doctor_id):
            return api_response(
                status_code=404,
                message="Doctor ID is not valid",
                error_code="DOCTOR_ID_NOT_FOUND",
                data=None,
            )

        schedule = await get_doctor_schedule_query(doctor_id)

        # The doctor already proved they exist by getting past require_role,
        # so an empty result means "no working hours set", not "no such user".
        # That is the normal state of a new account, not a failure.
        if schedule is None:
            return api_response(
                status_code=200,
                message="No schedule set yet. Set your working hours to start receiving appointments.",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Schedule retrieved successfully",
            data=serialize_data(schedule),
        )

    except Exception:
        logger.exception("Error in get_doctor_schedule")

        return api_response(
            status_code=500,
            message="Could not retrieve the schedule",
            error_code="SCHEDULE_FETCH_FAILED",
            data=None,
        )


async def get_doctor_schedule_query(doctor_id: str) -> dict | None:
    return await get_database().schedules.find_one(
        {
            "doctor_id": ObjectId(doctor_id),
            "is_active": True,  # a retired schedule reads the same as none set
        }
    )
