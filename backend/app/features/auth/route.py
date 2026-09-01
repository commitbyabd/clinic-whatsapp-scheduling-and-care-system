from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token
from app.schemas.user_login import UserLogin

from .v1.login import login_api

# tags is used to group this route in authentication in swagger ui documentation
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(login_data: UserLogin):
    user = await login_api(
        login_data.email,
        # this is used in pydantic to not log the password
        login_data.password.get_secret_value(),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=str(user["_id"]), role=user["role"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        # the dashboard greets the user by name, and the token carries only
        # the id and the role, so the name is sent once at sign in
        "full_name": user["full_name"],
    }
