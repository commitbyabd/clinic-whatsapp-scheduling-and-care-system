from bson import ObjectId
from app.core.database import get_database
from app.core.response import api_response
from app.db_functions.auth import get_user_by_email
from logging_config import logger


async def edit_receptionist(payload: dict):
    receptionist_id = payload.get("receptionist_id")
    full_name = payload.get("full_name")
    email = payload.get("email")

    try:
        # malformed id: the client sent something that is not an ObjectId at
        # all, which is a bad request rather than a missing record. The
        # isinstance half also narrows the id to str for the query below.
        if not isinstance(receptionist_id, str) or not ObjectId.is_valid(
            receptionist_id
        ):
            return api_response(
                status_code=400,
                message="Receptionist ID is not valid",
                error_code="INVALID_RECEPTIONIST_ID",
                data=None,
            )

        fields = {}

        if full_name is not None:
            fields["full_name"] = full_name

        if email is not None:
            existing = await get_user_by_email(email)

            # the email is free only if nobody owns it, or this receptionist already does
            if existing is not None and str(existing["_id"]) != receptionist_id:
                return api_response(
                    status_code=409,
                    message="A user with this email already exists",
                    error_code="EMAIL_TAKEN",
                    data=None,
                )

            fields["email"] = email.lower()

        if not fields:
            return api_response(
                status_code=400,
                message="No fields provided to update",
                error_code="NO_FIELDS_PROVIDED",
                data=None,
            )

        updated = await edit_receptionist_query(receptionist_id, fields)

        # the id was well formed, but it matches no receptionist — either
        # nothing owns it, or the account it owns is not a receptionist
        if not updated:
            return api_response(
                status_code=404,
                message="Receptionist not found",
                error_code="RECEPTIONIST_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Receptionist updated successfully",
            data=None,
        )

    except Exception:
        logger.exception("Error in edit_receptionist")

        return api_response(
            status_code=500,
            message="Could not update the receptionist",
            error_code="RECEPTIONIST_UPDATE_FAILED",
            data=None,
        )


async def edit_receptionist_query(receptionist_id: str, fields: dict) -> bool:
    result = await get_database().users.update_one(
        {
            "_id": ObjectId(receptionist_id),
            "role": "receptionist",
        },  # role guard: admins are untouchable
        {"$set": fields},
    )

    return result.matched_count == 1
