from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_booking_requests(status: str = "new", limit: int = 50):
    try:
        rows = await get_booking_requests_query(status, limit)

        return api_response(
            status_code=200,
            message=(
                "Booking requests retrieved successfully"
                if rows
                else f"No {status} booking requests"
            ),
            data=serialize_data([shape_booking_request(row) for row in rows]),
        )

    except Exception:
        logger.exception("Error in get_booking_requests")

        return api_response(
            status_code=500,
            message="Could not retrieve the booking requests",
            error_code="BOOKING_REQUESTS_FETCH_FAILED",
            data=None,
        )


def shape_booking_request(row: dict) -> dict:
    # built by hand so a field added to the document later never reaches the
    # screen by accident
    return {
        "_id": row["_id"],
        "whatsapp_number": row.get("whatsapp_number"),
        "patient_name": row.get("patient_name"),
        "returning_patient": row.get("returning_patient"),
        "reason": row.get("reason"),
        "symptom_text": row.get("symptom_text"),
        "suggested_specialization": row.get("suggested_specialization"),
        # the doctor and open time picked in the chat, when one was
        "requested_doctor_id": row.get("requested_doctor_id"),
        "requested_doctor_name": row.get("requested_doctor_name"),
        "requested_slot": row.get("requested_slot"),
        "preferred_time_text": row.get("preferred_time_text"),
        "status": row.get("status"),
        "created_at": row.get("created_at"),
    }


async def get_booking_requests_query(status: str, limit: int) -> list[dict]:
    # served by the (status, created_at) index in app/core/indexes.py
    cursor = (
        get_database()
        .booking_requests.find({"status": status})
        .sort("created_at", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
