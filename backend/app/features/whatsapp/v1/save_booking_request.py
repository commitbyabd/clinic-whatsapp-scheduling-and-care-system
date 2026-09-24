"""Turns a finished WhatsApp booking chat into a request for the front desk."""

from datetime import datetime, timezone

from bson import ObjectId

from app.core.database import get_database

WHATSAPP_PREFIX = "whatsapp:"


def booking_request_document(collected: dict[str, str], from_number: str) -> dict:
    return {
        "channel": "whatsapp",
        # Twilio sends "whatsapp:+923001234567"; patients are matched on the
        # bare number, and one number can belong to a whole family
        "whatsapp_number": from_number.removeprefix(WHATSAPP_PREFIX),
        # new and returning patients are both asked for it
        "patient_name": collected.get("name"),
        "returning_patient": collected.get("returning_patient"),
        "reason": collected.get("reason"),
        "symptom_text": collected.get("symptom_text"),
        "suggested_specialization": collected.get("specialization"),
        # The doctor and open time the patient picked in the chat. Asked for,
        # not held: the receptionist confirms it, or offers another.
        "requested_doctor_id": _doctor_id(collected.get("doctor_id")),
        "requested_doctor_name": collected.get("doctor_name"),
        "requested_slot": _slot(collected.get("requested_slot")),
        # free text such as "tomorrow at 9am", when no open time was picked
        "preferred_time_text": collected.get("preferred_datetime"),
        "status": "new",
        # filled in when the receptionist handles it
        "patient_id": None,
        "appointment_id": None,
        "handled_by": None,
        "handled_at": None,
        "created_at": datetime.now(timezone.utc),
    }


def _doctor_id(value: str | None) -> ObjectId | None:
    return ObjectId(value) if value and ObjectId.is_valid(value) else None


def _slot(value: str | None) -> datetime | None:
    # an ISO time with its offset, or "none" when the patient chose "None of
    # these"; stored in UTC like every other time
    try:
        moment = datetime.fromisoformat(value or "")
    except ValueError:
        return None
    return moment.astimezone(timezone.utc) if moment.tzinfo else None


async def save_booking_request_query(document: dict):
    return await get_database().booking_requests.insert_one(document)
