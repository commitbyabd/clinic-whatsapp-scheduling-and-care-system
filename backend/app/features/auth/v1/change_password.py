from app.core.database import get_database
from app.core.response import api_response
from app.core.security import (
    create_access_token,
    hash_password,
    password_changed_now,
    verify_password,
)
from logging_config import logger


async def change_password(user: dict, current_password: str, new_password: str):
    try:
        # the signed-in user arrives without its hash, so it is read here
        stored = await find_password_hash_query(user["_id"])

        if not stored or not verify_password(current_password, stored):
            return api_response(
                status_code=400,
                message="Your current password is not right",
                error_code="WRONG_PASSWORD",
                data=None,
            )

        if new_password == current_password:
            return api_response(
                status_code=400,
                message="Choose a password different from your current one",
                error_code="SAME_PASSWORD",
                data=None,
            )

        await set_password_query(user["_id"], hash_password(new_password))

        # Every session from before the change has now ended, this one
        # included, so it carries on with a fresh token.
        return api_response(
            status_code=200,
            message="Password changed",
            data={
                "access_token": create_access_token(str(user["_id"]), user["role"]),
                "token_type": "bearer",
            },
        )

    except Exception:
        logger.exception("Error in change_password")

        return api_response(
            status_code=500,
            message="Could not change the password",
            error_code="PASSWORD_CHANGE_FAILED",
            data=None,
        )


async def find_password_hash_query(user_id) -> str | None:
    row = await get_database().users.find_one({"_id": user_id}, {"password_hash": 1})
    return (row or {}).get("password_hash")


async def set_password_query(user_id, password_hash: str) -> None:
    await get_database().users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "password_hash": password_hash,
                "password_changed_at": password_changed_now(),
            }
        },
    )
