# Entry points for everything the receptionist dashboard can do.

from .cancel_appointment import cancel_appointment
from .decline_booking_request import decline_booking_request
from .get_booking_requests import get_booking_requests
from .get_day_appointments import get_day_appointments
from .get_doctors import get_doctors
from .get_free_slots import get_free_slots
from .get_matching_patients import get_matching_patients
from .reschedule_appointment import reschedule_appointment
from .schedule_booking_request import schedule_booking_request


async def get_booking_requests_api(status: str, limit: int):
    return await get_booking_requests(status, limit)


async def get_doctors_api():
    return await get_doctors()


async def get_free_slots_api(doctor_id: str, day):
    return await get_free_slots(doctor_id, day)


async def get_matching_patients_api(request_id: str):
    return await get_matching_patients(request_id)


async def schedule_booking_request_api(payload: dict):
    return await schedule_booking_request(payload)


async def decline_booking_request_api(
    request_id: str, receptionist_id: str, reason: str | None = None
):
    return await decline_booking_request(request_id, receptionist_id, reason)


async def get_day_appointments_api(day):
    return await get_day_appointments(day)


async def cancel_appointment_api(
    appointment_id: str, receptionist_id: str, reason: str | None
):
    return await cancel_appointment(appointment_id, receptionist_id, reason)


async def reschedule_appointment_api(payload: dict):
    return await reschedule_appointment(payload)
