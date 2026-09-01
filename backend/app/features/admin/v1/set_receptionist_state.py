from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from logging_config import logger


async def set_receptionist_state(receptionist_id: str, is_active: bool):
    # activating and deactivating are the same operation, only the wording differs
    if is_active:
        verb, action, failure_code = (
            "reactivated",
            "reactivate",
            "RECEPTIONIST_REACTIVATE_FAILED",
        )
    else:
        verb, action, failure_code = (
            "deactivated",
            "deactivate",
            "RECEPTIONIST_DEACTIVATE_FAILED",
        )

    try:
        # malformed id, treat the same as "not found"
        if not ObjectId.is_valid(receptionist_id):
            return api_response(
                status_code=404,
                message="Receptionist not found",
                error_code="RECEPTIONIST_NOT_FOUND",
                data=None,
            )

        result = await get_database().users.update_one(
            {
                "_id": ObjectId(receptionist_id),
                "role": "receptionist",
            },  # role guard: admins are untouchable
            {"$set": {"is_active": is_active}},
        )

        if result.matched_count == 0:
            return api_response(
                status_code=404,
                message="Receptionist not found",
                error_code="RECEPTIONIST_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message=f"Receptionist {verb} successfully",
            data=None,
        )

    except Exception:
        logger.exception("Error in set_receptionist_state")

        return api_response(
            status_code=500,
            message=f"Could not {action} the receptionist",
            error_code=failure_code,
            data=None,
        )
