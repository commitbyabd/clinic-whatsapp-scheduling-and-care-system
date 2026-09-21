"""Indexes the app's queries rely on, created at startup.

create_index does nothing when the index already exists, so this is safe to
run on every boot and adding one is a new line here.
"""

from pymongo import ASCENDING, DESCENDING

from app.core.database import get_database


async def ensure_indexes() -> None:
    db = get_database()

    # the receptionist inbox: one status at a time, newest first
    await db.booking_requests.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)]
    )
