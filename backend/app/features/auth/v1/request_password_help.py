"""A staff member who cannot sign in asks an admin to reset their password.

Nobody resets anybody's password here: the form only leaves a note for the
admin, who does the reset in the portal. So there is no link to steal and
no token to guess, and typing someone else's email achieves nothing.

The reply is the same whatever is typed, so the form cannot be used to find
out who has an account.
"""

from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.core.database import get_database
from app.core.response import api_response
from logging_config import logger

# The accounts an admin can reset from the portal. A request for an admin
# account would sit in the list with nothing anyone could do about it.
RESETTABLE_ROLES = ["doctor", "receptionist"]

SAME_REPLY = (
    "Thanks. If that email belongs to a staff account, our admin team will "
    "reset the password and get in touch."
)


async def request_password_help(email: str):
    try:
        user = await find_staff_query(email.strip().lower())

        # An unknown, deactivated or admin address leaves no note: there is
        # nothing an admin could do with it. The asker is told the same
        # either way. The email is personal data, so it stays out of the log.
        if user is None:
            logger.info("password help asked for an address with no staff account")
        else:
            await record_request_query(user)

        return api_response(status_code=200, message=SAME_REPLY, data=None)

    except Exception:
        logger.exception("Error in request_password_help")

        # Saying it failed tells the asker nothing about the account, and
        # not saying so would leave them waiting for help nobody heard about.
        return api_response(
            status_code=500,
            message="Sorry, we could not pass that on just now. Please call the clinic.",
            error_code="PASSWORD_HELP_FAILED",
            data=None,
        )


async def find_staff_query(email: str) -> dict | None:
    return await get_database().users.find_one(
        {"email": email, "role": {"$in": RESETTABLE_ROLES}, "is_active": True},
        {"full_name": 1, "email": 1, "role": 1},
    )


async def record_request_query(user: dict) -> None:
    """One open request per person: asking again bumps the count instead of
    filling the admin's list with copies."""
    now = datetime.now(timezone.utc)

    try:
        await get_database().password_requests.update_one(
            {"user_id": user["_id"], "status": "new"},
            {
                # a snapshot, so the list reads the same even if the account
                # is renamed afterwards
                "$set": {
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "role": user.get("role"),
                    "asked_at": now,
                },
                "$inc": {"times_asked": 1},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
    except DuplicateKeyError:
        # two taps on Send at once: the first one is the request
        logger.info("password help asked twice at once")
