"""Turns a finished WhatsApp booking chat into a request for the front desk."""

from datetime import datetime, timezone

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
        # free text such as "tomorrow at 9am"; the receptionist picks the slot
        "preferred_time_text": collected.get("preferred_datetime"),
        "status": "new",
        # filled in when the receptionist handles it
        "patient_id": None,
        "appointment_id": None,
        "handled_by": None,
        "handled_at": None,
        "created_at": datetime.now(timezone.utc),
    }


async def save_booking_request_query(document: dict):
    return await get_database().booking_requests.insert_one(document)
