from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role
from app.schemas.appointment_status_update import AppointmentStatusUpdate
from app.schemas.consultation_update import ConsultationUpdate
from app.schemas.doctor_schedule_update import DoctorScheduleUpdate
from app.schemas.patient_medical_update import PatientMedicalUpdate

from .v1.doctor_dashboard import (
    get_doctor_schedule_api,
    edit_doctor_schedule_api,
    get_appointments_api,
    save_consultation_api,
    set_appointment_status_api,
    edit_patient_medical_api,
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
# query matches on both. That pairing is what stops one doctor writing into
# another doctor's consultation.
#
# PUT: the whole write-up (diagnosis, vitals, prescriptions, follow-up and
# notes) arrives every time and replaces the last one.
@router.put("/appointments/{appointment_id}/consultation")
async def save_appointment_consultation(
    appointment_id: str,
    consultation: ConsultationUpdate,
    user: dict = Depends(require_role("doctor")),
):
    return await save_consultation_api(
        {
            "doctor_id": str(user["_id"]),
            "appointment_id": appointment_id,
            **consultation.model_dump(),
        }
    )


# How the visit went: completed or no_show, or back to booked to undo either.
@router.patch("/appointments/{appointment_id}/status")
async def save_appointment_status(
    appointment_id: str,
    update: AppointmentStatusUpdate,
    user: dict = Depends(require_role("doctor")),
):
    return await set_appointment_status_api(
        {
            "doctor_id": str(user["_id"]),
            "appointment_id": appointment_id,
            "status": update.status,
        }
    )


# Allergies, long-term conditions and blood group. Only doctors change these,
# and only for patients they have an appointment with.
@router.put("/patients/{patient_id}/medical")
async def save_patient_medical(
    patient_id: str,
    medical: PatientMedicalUpdate,
    user: dict = Depends(require_role("doctor")),
):
    return await edit_patient_medical_api(
        {
            "doctor_id": str(user["_id"]),
            "patient_id": patient_id,
            **medical.model_dump(),
        }
    )
