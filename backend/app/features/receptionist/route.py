from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import require_role

from .v1.receptionist_dashboard import get_booking_requests_api

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
