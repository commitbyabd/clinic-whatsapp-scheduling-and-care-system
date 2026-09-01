from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role
from app.schemas.appointment_notes_update import AppointmentNotesUpdate
from app.schemas.doctor_schedule_update import DoctorScheduleUpdate

from .v1.doctor_dashboard import (
    get_doctor_schedule_api,
    edit_doctor_schedule_api,
    get_appointments_api,
    edit_patient_detail_api,
)

router = APIRouter(prefix="/doctor", tags=["doctor-dashboard"])


# The admin routes discard the user because their target comes from the URL.
# Here the target IS the caller, so the id is taken off the token: a doctor
# cannot ask for somebody else's schedule because there is nothing to ask with.
@router.get("/schedule")
async def doctor_schedule(user: dict = Depends(require_role("doctor"))):
    return await get_doctor_schedule_api(str(user["_id"]))


# PUT, not POST: the whole week arrives every time and replaces what was there,
# so sending the same body twice leaves the schedule in the same state.
@router.put("/schedule")
async def save_doctor_schedule(
    schedule: DoctorScheduleUpdate,
    user: dict = Depends(require_role("doctor")),
):
    return await edit_doctor_schedule_api(
        {"doctor_id": str(user["_id"]), **schedule.model_dump()}
    )


# include_past=true brings finished days back, which is what a doctor writing up
# yesterday evening needs. Left out, the dashboard starts at this morning.
@router.get("/appointments")
async def doctor_appointments(
    include_past: bool = False,
    user: dict = Depends(require_role("doctor")),
):
    return await get_appointments_api(str(user["_id"]), include_past)


# Here the id DOES arrive in the URL, so the token id travels with it and the
# query matches on both. That pairing is what stops one doctor writing notes
# into another doctor's consultation.
@router.patch("/appointments/{appointment_id}/notes")
async def save_appointment_notes(
    appointment_id: str,
    notes: AppointmentNotesUpdate,
    user: dict = Depends(require_role("doctor")),
):
    return await edit_patient_detail_api(
        {
            "doctor_id": str(user["_id"]),
            "appointment_id": appointment_id,
            **notes.model_dump(),
        }
    )
