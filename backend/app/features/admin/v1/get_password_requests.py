from pymongo import DESCENDING

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

LIMIT = 50


async def get_password_requests():
    """Staff who asked for a password reset from the sign-in page, the one
    who asked most recently first."""
    try:
        rows = await get_password_requests_query()

        return api_response(
            status_code=200,
            message=(
                "Password requests retrieved successfully"
                if rows
                else "No password requests"
            ),
            data=serialize_data([shape_password_request(row) for row in rows]),
        )

    except Exception:
        logger.exception("Error in get_password_requests")

        return api_response(
            status_code=500,
            message="Could not retrieve the password requests",
            error_code="PASSWORD_REQUESTS_FETCH_FAILED",
            data=None,
        )


def shape_password_request(row: dict) -> dict:
    # built by hand so a field added to the document later never reaches
    # the screen by accident
    return {
        "_id": row["_id"],
        # the account to reset, which the Reset password dialog needs
        "user_id": row.get("user_id"),
        "email": row.get("email"),
        "full_name": row.get("full_name"),
        "role": row.get("role"),
        # asking again bumps this rather than adding a row
        "times_asked": row.get("times_asked", 1),
        "asked_at": row.get("asked_at"),
    }


async def get_password_requests_query() -> list[dict]:
    cursor = (
        get_database()
        .password_requests.find({"status": "new"})
        .sort("asked_at", DESCENDING)
        .limit(LIMIT)
    )
    return await cursor.to_list(length=LIMIT)
