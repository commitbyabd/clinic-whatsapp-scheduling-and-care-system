"""The clinic's doctors, their weekly hours and open times, as the chatbot
sees them.

The chatbot still knows nothing about Mongo: the app registers a provider
at startup (app/features/whatsapp/v1/clinic_directory.py). With none
registered, or when it fails, the booking chat falls back to asking for a
time in the patient's own words, the way it always did.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from chatbot.classifier import SPECIALIZATIONS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Doctor:
    id: str
    name: str
    specialization: str
    # first come, first served: patients just come in during the hours
    walk_in: bool
    # (day_of_week, "09:00", "13:00"), 0 being Monday
    hours: tuple[tuple[int, str, str], ...]


class Directory(Protocol):
    def doctors(self, specialization: str | None = None) -> list[Doctor]: ...
    def doctor(self, doctor_id: str) -> Doctor | None: ...
    # the next free slots, soonest first, as aware datetimes in clinic time
    def open_times(self, doctor_id: str, limit: int) -> list[datetime]: ...


_provider: Directory | None = None


def register(provider: Directory | None) -> None:
    global _provider
    _provider = provider


# Each lookup returns None when there is no directory or it failed, so the
# booking chat can fall back rather than break. An empty list means it
# worked and found nothing.


def find_doctors(specialization: str | None = None) -> list[Doctor] | None:
    if _provider is None:
        return None
    try:
        return _provider.doctors(specialization)
    except Exception as exc:
        # the type only: a database error can quote patient data
        logger.error("doctor directory failed (%s)", type(exc).__name__)
        return None


def find_doctor(doctor_id: str) -> Doctor | None:
    if _provider is None:
        return None
    try:
        return _provider.doctor(doctor_id)
    except Exception as exc:
        logger.error("doctor directory failed (%s)", type(exc).__name__)
        return None


def find_open_times(doctor_id: str, limit: int) -> list[datetime] | None:
    if _provider is None:
        return None
    try:
        return _provider.open_times(doctor_id, limit)
    except Exception as exc:
        logger.error("doctor directory failed (%s)", type(exc).__name__)
        return None


# --- wording -------------------------------------------------------------

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _clock(hhmm: str) -> tuple[str, str]:
    """ "17:30" -> ("5:30", "PM")"""
    hours, minutes = (int(part) for part in hhmm.split(":"))
    number = str(hours % 12 or 12) + (f":{minutes:02d}" if minutes else "")
    return number, "AM" if hours < 12 else "PM"


def _span(start: str, end: str) -> str:
    """ "09:00", "13:00" -> "9 AM–1 PM"; "17:00", "20:00" -> "5–8 PM" """
    (first, first_half), (last, last_half) = _clock(start), _clock(end)
    if first_half == last_half:
        return f"{first}–{last} {last_half}"
    return f"{first} {first_half}–{last} {last_half}"


def _days(days: list[int]) -> str:
    """[0, 1, 2, 4] -> "Mon–Wed, Fri": runs of three or more get a dash"""
    runs: list[list[int]] = []
    for day in sorted(days):
        if runs and day == runs[-1][-1] + 1:
            runs[-1].append(day)
        else:
            runs.append([day])

    parts = []
    for run in runs:
        if len(run) >= 3:
            parts.append(f"{DAY_NAMES[run[0]]}–{DAY_NAMES[run[-1]]}")
        else:
            parts.extend(DAY_NAMES[day] for day in run)
    return ", ".join(parts)


def describe_hours(hours: tuple[tuple[int, str, str], ...]) -> str:
    """The week in one line: "Mon–Sat, 9 AM–1 PM and 5–8 PM". Days that
    share the same hours are grouped, and groups are joined with "; "."""
    by_day: dict[int, list[tuple[str, str]]] = {}
    for day, start, end in sorted(hours):
        by_day.setdefault(day, []).append((start, end))

    groups: dict[tuple[tuple[str, str], ...], list[int]] = {}
    for day, blocks in sorted(by_day.items()):
        groups.setdefault(tuple(blocks), []).append(day)

    return "; ".join(
        f"{_days(days)}, {' and '.join(_span(start, end) for start, end in blocks)}"
        for blocks, days in groups.items()
    )


def slot_label(moment: datetime) -> str:
    """ "Tue 23 Sep, 9:00 AM", in whatever timezone the moment carries (the
    directory hands times over in clinic time)"""
    time = moment.strftime("%I:%M %p").lstrip("0")
    return f"{DAY_NAMES[moment.weekday()]} {moment.day} {moment:%b}, {time}"


# The words patients use for each department, beside its own name. Checked
# with word boundaries, so "ent" does not match inside "appointment".
_DEPARTMENT_WORDS = {
    "General Physician": ("general physician", "physician", "gp", "general doctor", "family doctor"),
    "Dermatologist": ("dermatologist", "dermatology", "skin doctor", "skin specialist"),
    "Pulmonologist": ("pulmonologist", "chest specialist", "lung specialist"),
    "Neurologist": ("neurologist", "neurology"),
    "Orthopedist": ("orthopedist", "orthopaedic", "orthopedic", "bone specialist"),
    "ENT Specialist": ("ent specialist", "ent"),
    "Gynecologist": ("gynecologist", "gynaecologist", "gynae", "lady doctor"),
    "Pediatrician": ("pediatrician", "paediatrician", "child specialist", "children's doctor"),
    "General Surgeon": ("general surgeon", "surgeon"),
    "Urologist": ("urologist", "urology"),
    "Cardiologist": ("cardiologist", "heart specialist", "heart doctor"),
    "Endocrinologist": ("endocrinologist", "diabetes specialist"),
}
assert set(_DEPARTMENT_WORDS) == set(SPECIALIZATIONS), "a department is missing"

_DEPARTMENT_PATTERNS = [
    (
        department,
        re.compile(
            r"\b(?:" + "|".join(re.escape(word) for word in words) + r")s?\b",
            re.IGNORECASE,
        ),
    )
    for department, words in _DEPARTMENT_WORDS.items()
]


def department_in(message: str) -> str | None:
    """The department a message names, such as "general physician" in "what
    is the schedule of your general physician?", or None."""
    for department, pattern in _DEPARTMENT_PATTERNS:
        if pattern.search(message):
            return department
    return None
