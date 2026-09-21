from datetime import datetime

from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

# more than any family sharing one phone, so the list stays bounded
MATCH_LIMIT = 20


async def get_matching_patients(request_id: str):
    try:
        if not ObjectId.is_valid(request_id):
            return api_response(
                status_code=400,
                message="Booking request ID is not valid",
                error_code="INVALID_REQUEST_ID",
                data=None,
            )

        request = await find_request_number_query(request_id)

        if request is None:
            return api_response(
                status_code=404,
                message="Booking request not found",
                error_code="REQUEST_NOT_FOUND",
                data=None,
            )

        # Without a number there is nothing to match on. Asking Mongo for
        # {"whatsapp_number": None} would return every patient without one.
        number = request.get("whatsapp_number")
        rows = await matching_patients_query(number) if number else []

        return api_response(
            status_code=200,
            message=(
                "Patients with this number retrieved successfully"
                if rows
                else "No patients with this number yet"
            ),
            data=serialize_data([shape_patient(row) for row in rows]),
        )

    except Exception:
        logger.exception("Error in get_matching_patients")

        return api_response(
            status_code=500,
            message="Could not look up the patients",
            error_code="PATIENT_MATCH_FAILED",
            data=None,
        )


def shape_patient(row: dict) -> dict:
    born = row.get("date_of_birth")

    # enough to tell family members apart, and nothing medical
    return {
        "_id": row["_id"],
        "full_name": row.get("full_name"),
        # the day alone: a birthday has no time of day to shift between zones
        "date_of_birth": born.date() if isinstance(born, datetime) else None,
        "gender": row.get("gender"),
    }


async def find_request_number_query(request_id: str) -> dict | None:
    return await get_database().booking_requests.find_one(
        {"_id": ObjectId(request_id)}, {"whatsapp_number": 1}
    )


async def matching_patients_query(whatsapp_number: str) -> list[dict]:
    cursor = (
        get_database()
        .patients.find(
            {"whatsapp_number": whatsapp_number, "is_active": True},
            {"full_name": 1, "date_of_birth": 1, "gender": 1},
        )
        .sort("full_name", 1)
        .limit(MATCH_LIMIT)
    )
    return await cursor.to_list(length=MATCH_LIMIT)
