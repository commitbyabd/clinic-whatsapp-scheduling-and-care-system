"""Slot maths shared by booking, moving and the WhatsApp chat: which times a
doctor works on a clinic day, and which of those are still free. Pure
functions, so the async API and the chatbot's blocking reads both use them."""

from datetime import date, datetime, timedelta, timezone

from app.core.clinic_time import as_utc, clinic_time

# the schedule schema's default, for a schedule saved without one
DEFAULT_SLOT_MINUTES = 30

# The statuses that hold a slot. A cancelled visit gives its slot back, and
# completed and no_show visits are already in the past.
ACTIVE_STATUSES = ["booked", "confirmed"]


def slot_minutes(schedule: dict | None) -> int:
    return (schedule or {}).get("slot_minutes") or DEFAULT_SLOT_MINUTES


def working_slots(
    schedule: dict | None, day: date
) -> tuple[list[datetime], str | None]:
    """Every slot start the doctor works on a clinic day, in UTC.

    When there are none, the second value says why, for the receptionist.
    """
    if not schedule:
        return [], "This doctor has not set their working hours yet"

    # a day off is stored as midnight UTC of that day
    days_off = {as_utc(day_off).date() for day_off in schedule.get("blackout_dates") or []}
    if day in days_off:
        return [], "The doctor is not working on this day"

    step = timedelta(minutes=slot_minutes(schedule))
    starts = []

    for block in schedule.get("working_hours") or []:
        # 0 is Monday in the schedule and in Python alike
        if block.get("day_of_week") != day.weekday():
            continue

        start = clinic_time(day, block["start_time"])
        end = clinic_time(day, block["end_time"])

        # a slot has to finish by the end of its block
        while start + step <= end:
            starts.append(start.astimezone(timezone.utc))
            start += step

    if not starts:
        return [], "The doctor does not work on this day"

    return sorted(starts), None


def free_slots(
    starts: list[datetime], booked: list[dict], minutes: int, now: datetime
) -> list[datetime]:
    """The starts still open: not in the past, and not overlapping a booking."""
    step = timedelta(minutes=minutes)

    taken = [
        (
            as_utc(row["scheduled_for"]),
            timedelta(minutes=row.get("duration_minutes") or minutes),
        )
        for row in booked
    ]

    # Overlap rather than equal start times, so a visit booked before the
    # doctor changed their slot length still blocks every slot it covers.
    return [
        start
        for start in starts
        if start > now
        and not any(
            begins < start + step and start < begins + length
            for begins, length in taken
        )
    ]
