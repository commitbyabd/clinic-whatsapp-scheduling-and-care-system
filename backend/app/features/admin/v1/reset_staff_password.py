from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from app.core.security import hash_password, password_changed_now
from logging_config import logger

# the accounts an admin manages; other admins are not reset from here
STAFF_ROLES = ["doctor", "receptionist"]


async def reset_staff_password(user_id: str, new_password: str):
    if not ObjectId.is_valid(user_id):
        return api_response(
            status_code=400,
            message="User ID is not valid",
            error_code="INVALID_USER_ID",
            data=None,
        )

    try:
        result = await reset_staff_password_query(user_id, hash_password(new_password))

        if result.matched_count == 0:
            return api_response(
                status_code=404,
                message="Staff member not found",
                error_code="USER_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Password reset. Anyone signed in with the old one has been signed out.",
            data={"id": user_id},
        )

    except Exception:
        logger.exception("Error in reset_staff_password")

        return api_response(
            status_code=500,
            message="Could not reset the password",
            error_code="PASSWORD_RESET_FAILED",
            data=None,
        )


async def reset_staff_password_query(user_id: str, password_hash: str):
    # password_changed_at ends every session signed in with the old password
    return await get_database().users.update_one(
        {"_id": ObjectId(user_id), "role": {"$in": STAFF_ROLES}},
        {
            "$set": {
                "password_hash": password_hash,
                "password_changed_at": password_changed_now(),
            }
        },
    )
