from app.core.database import get_database
import bson


async def get_user_by_email(email: str) -> dict | None:
    # converting to ensure the lookup is case-insensitive, as email addresses are generally treated as such
    return await get_database().users.find_one({"email": email.lower()})
