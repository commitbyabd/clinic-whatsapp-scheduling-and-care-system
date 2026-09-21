# Entry points for everything the receptionist dashboard can do.

from .get_booking_requests import get_booking_requests


async def get_booking_requests_api(status: str, limit: int):
    return await get_booking_requests(status, limit)
