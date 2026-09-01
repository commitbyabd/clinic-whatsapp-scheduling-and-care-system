# This library helps us to handle token errors later in the code in this module
import jwt
from bson import ObjectId
from app.core.database import get_database
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_database().users.find_one(
        {"_id": ObjectId(payload["sub"])},
        # we don't want to return the password hash to the user, so we exclude it from the returned document
        {"password_hash": 0},
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user


# Checks whether the logged-in user has one of the roles allowed for this endpoint
def require_role(*allowed_roles: str):
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return user

    # a function that creates and returns new objects, typically instances of a class
    return role_checker
