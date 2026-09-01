from .user_login import authenticate_user


async def login_api(email: str, password: str):
    return await authenticate_user(email, password)
