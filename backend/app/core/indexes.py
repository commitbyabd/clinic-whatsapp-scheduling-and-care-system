"""Indexes the app's queries rely on, created at startup.

create_index does nothing when the index already exists, so this is safe to
run on every boot and adding one is a new line here.
"""

from pymongo import ASCENDING, DESCENDING

from app.core.database import get_database
from chatbot.conversation import STATE_TTL


async def ensure_indexes() -> None:
    db = get_database()

    # the receptionist inbox: one status at a time, newest first
    await db.booking_requests.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)]
    )

    # patients are matched by the number a booking came from
    await db.patients.create_index("whatsapp_number")

    # the admin's password requests: the ones still waiting, newest first,
    # and one open request per person however often they press Send
    await db.password_requests.create_index(
        [("status", ASCENDING), ("asked_at", DESCENDING)]
    )
    await db.password_requests.create_index(
        "user_id",
        unique=True,
        partialFilterExpression={"status": "new"},
        name="one_open_password_request_per_user",
    )

    # one chat state per patient, deleted a day after their last message
    await db.conversation_states.create_index("whatsapp_number", unique=True)
    await db.conversation_states.create_index(
        "updated_at", expireAfterSeconds=int(STATE_TTL.total_seconds())
    )

    # One active appointment per doctor per start time. The slot check stops
    # this too; the index is what stops two receptionists booking the same
    # slot at the same moment. Last, because an old duplicate in the data
    # makes it fail, and the ones above must still be created.
    await db.appointments.create_index(
        [("doctor_id", ASCENDING), ("scheduled_for", ASCENDING)],
        unique=True,
        partialFilterExpression={"status": {"$in": ["booked", "confirmed"]}},
        name="one_active_appointment_per_slot",
    )
