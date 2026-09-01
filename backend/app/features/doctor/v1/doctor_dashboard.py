# This is the file which will be the middleware of all of the functions that
# our doctor dashboard will be able to perform.

from .get_doctor_schedule import get_doctor_schedule
from .edit_doctor_schedule import edit_doctor_schedule
from .get_appointments import get_appointments
from .edit_patient_detail import edit_patient_detail


async def get_doctor_schedule_api(doctor_id: str):
    return await get_doctor_schedule(doctor_id)


async def edit_doctor_schedule_api(payload: dict):
    return await edit_doctor_schedule(payload)


async def get_appointments_api(doctor_id: str, include_past: bool = False):
    return await get_appointments(doctor_id, include_past)


async def edit_patient_detail_api(payload: dict):
    return await edit_patient_detail(payload)
