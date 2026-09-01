from fastapi import HTTPException, status
from app.core.response import api_response
from app.core.security import create_access_token, verify_password
from app.db_functions.auth import get_user_by_email


async def authenticate_user(email: str, password: str) -> dict | None:

    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active", False):
        return None
    return user
