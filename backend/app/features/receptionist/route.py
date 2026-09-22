from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import require_role
from app.schemas.appointment_change import AppointmentCancel, AppointmentReschedule
from app.schemas.booking_schedule import BookingDecline, BookingSchedule

from .v1.receptionist_dashboard import (
    cancel_appointment_api,
    decline_booking_request_api,
    get_booking_requests_api,
    get_day_appointments_api,
    get_doctors_api,
    get_free_slots_api,
    get_matching_patients_api,
    reschedule_appointment_api,
    schedule_booking_request_api,
)

router = APIRouter(prefix="/receptionist", tags=["receptionist-dashboard"])


# The inbox. WhatsApp booking chats land here as "new" until a receptionist
# schedules or declines them; the other statuses are the history.
@router.get("/booking-requests")
async def booking_requests(
    status: Literal["new", "scheduled", "declined", "cancelled"] = "new",
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(require_role("receptionist")),
):
    return await get_booking_requests_api(status, limit)


# The patients already registered under the request's WhatsApp number. The
# number is read from the request, so it never goes in a URL, where access
# logs would keep it.
@router.get("/booking-requests/{request_id}/patients")
async def matching_patients(
    request_id: str,
    _: dict = Depends(require_role("receptionist")),
):
    return await get_matching_patients_api(request_id)


# POST because it creates an appointment, and a patient when they are new.
# The receptionist's id comes off the token and is saved as who booked it.
@router.post("/booking-requests/{request_id}/schedule")
async def schedule_request(
    request_id: str,
    booking: BookingSchedule,
    user: dict = Depends(require_role("receptionist")),
):
    return await schedule_booking_request_api(
        {
            "request_id": request_id,
            "receptionist_id": str(user["_id"]),
            **booking.model_dump(),
        }
    )


@router.patch("/booking-requests/{request_id}/decline")
async def decline_request(
    request_id: str,
    # optional body: a decline without a reason sends none
    decline: BookingDecline | None = None,
    user: dict = Depends(require_role("receptionist")),
):
    return await decline_booking_request_api(
        request_id, str(user["_id"]), decline.reason if decline else None
    )


# A clinic day's visits across every doctor, cancelled ones included.
@router.get("/appointments")
async def day_appointments(
    day: date = Query(..., alias="date"),
    _: dict = Depends(require_role("receptionist")),
):
    return await get_day_appointments_api(day)


# Cancelling keeps the visit on record and frees its slot.
@router.patch("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    cancel: AppointmentCancel | None = None,
    user: dict = Depends(require_role("receptionist")),
):
    return await cancel_appointment_api(
        appointment_id, str(user["_id"]), cancel.reason if cancel else None
    )


# To another free time, with the same doctor or a different one.
@router.patch("/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    move: AppointmentReschedule,
    user: dict = Depends(require_role("receptionist")),
):
    return await reschedule_appointment_api(
        {
            "appointment_id": appointment_id,
            "receptionist_id": str(user["_id"]),
            **move.model_dump(),
        }
    )


@router.get("/doctors")
async def doctors(_: dict = Depends(require_role("receptionist"))):
    return await get_doctors_api()


# Worked out on every call from the doctor's weekly hours minus what is
# already booked. Free slots are never stored.
@router.get("/doctors/{doctor_id}/slots")
async def doctor_free_slots(
    doctor_id: str,
    day: date = Query(..., alias="date"),
    _: dict = Depends(require_role("receptionist")),
):
    return await get_free_slots_api(doctor_id, day)
