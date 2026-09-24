"""Taking a password request off the admin's list.

Either because the admin reset the password (that closes it by itself) or
because there was nothing to do, such as a colleague sorted out by phone.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from logging_config import logger


async def close_password_request(request_id: str, admin_id: str):
    try:
        if not ObjectId.is_valid(request_id):
            return api_response(
                status_code=400,
                message="Request ID is not valid",
                error_code="INVALID_REQUEST_ID",
                data=None,
            )

        closed = await close_password_request_query(request_id, admin_id)

        # already handled by another admin, or never existed
        if not closed:
            return api_response(
                status_code=404,
                message="That request is no longer waiting",
                error_code="PASSWORD_REQUEST_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Request closed",
            data={"id": request_id},
        )

    except Exception:
        logger.exception("Error in close_password_request")

        return api_response(
            status_code=500,
            message="Could not close the request",
            error_code="PASSWORD_REQUEST_CLOSE_FAILED",
            data=None,
        )


async def close_password_request_query(request_id: str, admin_id: str) -> bool:
    result = await get_database().password_requests.update_one(
        {"_id": ObjectId(request_id), "status": "new"},
        {"$set": _handled(admin_id)},
    )
    return result.matched_count == 1


async def close_requests_for_user(user_id: str, admin_id: str | None) -> None:
    """Called after a reset, so answering the request closes it whichever
    list the admin did it from."""
    await get_database().password_requests.update_many(
        {"user_id": ObjectId(user_id), "status": "new"},
        {"$set": _handled(admin_id)},
    )


def _handled(admin_id: str | None) -> dict:
    return {
        "status": "handled",
        "handled_by": ObjectId(admin_id) if admin_id else None,
        "handled_at": datetime.now(timezone.utc),
    }
