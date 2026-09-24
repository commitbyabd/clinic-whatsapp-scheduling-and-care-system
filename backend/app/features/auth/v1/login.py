from .change_password import change_password
from .request_password_help import request_password_help
from .user_login import authenticate_user


async def login_api(email: str, password: str):
    return await authenticate_user(email, password)


async def change_password_api(user: dict, current_password: str, new_password: str):
    return await change_password(user, current_password, new_password)


async def request_password_help_api(email: str):
    return await request_password_help(email)
