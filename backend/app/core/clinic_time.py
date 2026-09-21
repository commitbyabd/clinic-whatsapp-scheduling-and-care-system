"""The clinic's clock. The database stores UTC; people think in clinic time."""

from datetime import date, datetime, time, timedelta, timezone

# Pakistan sits at UTC+5 all year and never shifts for daylight saving.
# Belongs in settings the day a second clinic in another country appears.
CLINIC_TZ = timezone(timedelta(hours=5))


def as_utc(moment: datetime) -> datetime:
    # Mongo hands datetimes back without a timezone, but they are stored in UTC
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def clinic_time(day: date, hhmm: str) -> datetime:
    """A wall-clock time such as "09:30" on a clinic day."""
    hour, minute = (int(part) for part in hhmm.split(":"))
    return datetime.combine(day, time(hour, minute), tzinfo=CLINIC_TZ)


def clinic_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Midnight to midnight of a clinic day, in UTC."""
    start = datetime.combine(day, time.min, tzinfo=CLINIC_TZ)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
