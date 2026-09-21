from datetime import datetime, time, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.clinic_time import CLINIC_TZ
from app.core.database import get_database, run_in_transaction
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

from .get_free_slots import (
    booked_query,
    find_doctor_query,
    find_schedule_query,
    free_slots,
    slot_minutes,
    working_slots,
)

SLOT_GONE = "That time is no longer free. Pick another slot."
ALREADY_HANDLED = "This request has already been handled"


class BookingRefused(Exception):
    """Raised inside the transaction: it undoes the transaction and becomes
    the reply."""

    def __init__(self, status_code: int, message: str, error_code: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_code = error_code


async def schedule_booking_request(payload: dict):
    ids = [
        payload.get("request_id"),
        payload.get("receptionist_id"),
        payload.get("doctor_id"),
    ]
    if payload.get("patient_id") is not None:
        ids.append(payload["patient_id"])

    if not all(isinstance(value, str) and ObjectId.is_valid(value) for value in ids):
        return api_response(
            status_code=400,
            message="An ID in this booking is not valid",
            error_code="INVALID_ID",
            data=None,
        )

    async def work(session):
        return await book(payload, session)

    try:
        # The patient, the appointment and the request's new status are saved
        # together or not at all, so a failure halfway leaves nothing behind.
        appointment = await run_in_transaction(work)

    except BookingRefused as refused:
        return api_response(
            status_code=refused.status_code,
            message=refused.message,
            error_code=refused.error_code,
            data=None,
        )

    except DuplicateKeyError:
        # the unique index caught two bookings of one slot at the same moment
        return api_response(
            status_code=409,
            message=SLOT_GONE,
            error_code="SLOT_NOT_FREE",
            data=None,
        )

    except Exception:
        logger.exception("Error in schedule_booking_request")

        return api_response(
            status_code=500,
            message="Could not book the appointment",
            error_code="SCHEDULE_FAILED",
            data=None,
        )

    return api_response(
        status_code=201,
        message="Appointment booked",
        data=serialize_data(
            {
                "_id": appointment["_id"],
                "patient_id": appointment["patient_id"],
                "doctor_id": appointment["doctor_id"],
                "scheduled_for": appointment["scheduled_for"],
                "duration_minutes": appointment["duration_minutes"],
                "status": appointment["status"],
            }
        ),
    )


async def book(payload: dict, session) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    starts_at = payload["starts_at"].astimezone(timezone.utc)

    request = await db.booking_requests.find_one(
        {"_id": ObjectId(payload["request_id"])}, session=session
    )
    if request is None:
        raise BookingRefused(404, "Booking request not found", "REQUEST_NOT_FOUND")
    if request.get("status") != "new":
        raise BookingRefused(409, ALREADY_HANDLED, "REQUEST_ALREADY_HANDLED")

    doctor = await find_doctor_query(payload["doctor_id"], session)
    if doctor is None:
        raise BookingRefused(404, "Doctor not found", "DOCTOR_NOT_FOUND")

    # Checked again rather than trusted: the list the receptionist picked
    # from may be minutes old.
    schedule = await find_schedule_query(payload["doctor_id"], session)
    day = starts_at.astimezone(CLINIC_TZ).date()
    starts, _ = working_slots(schedule, day)
    booked = await booked_query(payload["doctor_id"], day, session)
    minutes = slot_minutes(schedule)

    if starts_at not in free_slots(starts, booked, minutes, now):
        raise BookingRefused(409, SLOT_GONE, "SLOT_NOT_FREE")

    patient_id = await resolve_patient(payload, request, now, session)

    appointment = appointment_document(
        request, doctor, patient_id, starts_at, minutes, payload["receptionist_id"], now
    )
    await db.appointments.insert_one(appointment, session=session)

    marked = await db.booking_requests.update_one(
        # status in the filter as well, so a request someone else handled a
        # moment ago is never handled twice
        {"_id": request["_id"], "status": "new"},
        {
            "$set": {
                "status": "scheduled",
                "patient_id": patient_id,
                "appointment_id": appointment["_id"],
                "handled_by": ObjectId(payload["receptionist_id"]),
                "handled_at": now,
            }
        },
        session=session,
    )
    if marked.matched_count == 0:
        raise BookingRefused(409, ALREADY_HANDLED, "REQUEST_ALREADY_HANDLED")

    return appointment


async def resolve_patient(payload: dict, request: dict, now: datetime, session) -> ObjectId:
    db = get_database()

    if payload.get("patient_id"):
        patient = await db.patients.find_one(
            {"_id": ObjectId(payload["patient_id"]), "is_active": True},
            {"_id": 1},
            session=session,
        )
        if patient is None:
            raise BookingRefused(404, "Patient not found", "PATIENT_NOT_FOUND")
        return patient["_id"]

    patient = patient_document(
        payload["new_patient"], request.get("whatsapp_number"), now
    )
    await db.patients.insert_one(patient, session=session)
    return patient["_id"]


def patient_document(details: dict, whatsapp_number: str | None, now: datetime) -> dict:
    born = details.get("date_of_birth")

    return {
        "_id": ObjectId(),
        "full_name": details["full_name"],
        "preferred_name": None,
        # midnight UTC, the way schedules store a whole day
        "date_of_birth": (
            datetime.combine(born, time.min, tzinfo=timezone.utc) if born else None
        ),
        "gender": details.get("gender"),
        # the number the booking came from, which a family can share
        "whatsapp_number": whatsapp_number,
        # medical fields start empty, and only doctors fill them in
        "allergies": [],
        "chronic_conditions": [],
        "blood_group": None,
        "notes": "",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def appointment_document(
    request: dict,
    doctor: dict,
    patient_id: ObjectId,
    starts_at: datetime,
    minutes: int,
    receptionist_id: str,
    now: datetime,
) -> dict:
    return {
        "_id": ObjectId(),
        "doctor_id": doctor["_id"],
        "patient_id": patient_id,
        "scheduled_for": starts_at,
        "duration_minutes": minutes,
        # "confirmed" is kept for the patient saying they will come
        "status": "booked",
        "reason": request.get("reason"),
        # the patient's own words from WhatsApp, for the doctor to read first
        "symptom_summary": request.get("symptom_text"),
        "doctor_notes": "",
        # kept on the visit, so its history still shows who saw the patient
        # if that doctor's account changes later
        "doctor_snapshot": {"full_name": doctor.get("full_name")},
        "specialization": doctor.get("specialization"),
        "request_id": request["_id"],
        "booked_by": ObjectId(receptionist_id),
        "created_at": now,
        "updated_at": now,
    }
