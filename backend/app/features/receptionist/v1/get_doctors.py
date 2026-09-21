from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_doctors():
    try:
        rows = await get_doctors_query()

        return api_response(
            status_code=200,
            message=(
                "Doctors retrieved successfully" if rows else "No active doctors yet"
            ),
            data=serialize_data(rows),
        )

    except Exception:
        logger.exception("Error in get_doctors")

        return api_response(
            status_code=500,
            message="Could not retrieve the doctors",
            error_code="DOCTORS_FETCH_FAILED",
            data=None,
        )


async def get_doctors_query() -> list[dict]:
    # name and department only: the receptionist is choosing who to book with
    cursor = (
        get_database()
        .users.find(
            {"role": "doctor", "is_active": True},
            {"full_name": 1, "specialization": 1},
        )
        .sort("full_name", 1)
    )
    return await cursor.to_list(length=None)
