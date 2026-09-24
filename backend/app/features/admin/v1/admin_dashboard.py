# This is the file which will be the middleware of all of the functions that
# out admin dashboard will be able to perform on doctors and receptionists.

from .get_doctor_list import get_doctor_list
from .get_one_doctor import get_one_doctor
from .set_doctor_state import set_doctor_state
from .get_receptionist_list import get_receptionist_list
from .get_one_receptionist import get_one_receptionist
from .set_receptionist_state import set_receptionist_state
from .add_doctor import add_doctor
from .add_receptionist import add_receptionist
from .edit_doctor import edit_doctor
from .edit_receptionist import edit_receptionist
from .get_deactivated_users import get_deactivated_users
from .reset_staff_password import reset_staff_password
from .get_password_requests import get_password_requests
from .close_password_request import close_password_request


async def doctor_list_api():
    return await get_doctor_list()


async def get_one_doctor_api(doctor_id: str):
    return await get_one_doctor(doctor_id)


async def deactivate_doctor_api(doctor_id: str):
    return await set_doctor_state(doctor_id, is_active=False)


async def edit_doctor_api(payload: dict):
    return await edit_doctor(payload)


async def reactivate_doctor_api(doctor_id: str):
    return await set_doctor_state(doctor_id, is_active=True)


async def add_doctor_api(payload: dict):
    return await add_doctor(payload)


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


async def receptionist_list_api():
    return await get_receptionist_list()


async def get_one_receptionist_api(receptionist_id: str):
    return await get_one_receptionist(receptionist_id)


async def deactivate_receptionist_api(receptionist_id: str):
    return await set_receptionist_state(receptionist_id, is_active=False)


async def reactivate_receptionist_api(receptionist_id: str):
    return await set_receptionist_state(receptionist_id, is_active=True)


async def add_receptionist_api(payload: dict):
    return await add_receptionist(payload)


async def edit_receptionist_api(payload: dict):
    return await edit_receptionist(payload)


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


async def get_deactivated_users_api():
    return await get_deactivated_users()


async def reset_staff_password_api(user_id: str, new_password: str, admin_id: str = ""):
    return await reset_staff_password(user_id, new_password, admin_id)


async def password_requests_api():
    return await get_password_requests()


async def close_password_request_api(request_id: str, admin_id: str):
    return await close_password_request(request_id, admin_id)
