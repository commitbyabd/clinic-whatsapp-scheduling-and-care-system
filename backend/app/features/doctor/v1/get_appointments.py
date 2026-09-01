from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger

# A patient carries their whole life in this collection. The doctor screen only
# needs what helps them treat the person in front of them, so the shape below is
# built by hand: adding a field to `patients` must never leak it into the API by
# accident.
HISTORY_LIMIT = 20

# The clinic is in Pakistan, which sits at UTC+5 all year and never shifts for
# daylight saving. "Yesterday" has to mean yesterday to the doctor standing in
# the building, so the cut-off is worked out here and then converted to UTC.
# Belongs in settings the day a second clinic in another country appears.
CLINIC_TZ = timezone(timedelta(hours=5))


async def get_appointments(doctor_id: str, include_past: bool = False):
    try:
        if not isinstance(doctor_id, str) or not ObjectId.is_valid(doctor_id):
            return api_response(
                status_code=400,
                message="Doctor ID is not valid",
                error_code="INVALID_DOCTOR_ID",
                data=None,
            )

        rows = await get_appointments_query(doctor_id, include_past)

        empty_message = (
            "No appointments booked yet"
            if include_past
            else "Nothing left on the calendar from today onwards"
        )

        return api_response(
            status_code=200,
            message="Appointments retrieved successfully" if rows else empty_message,
            data=serialize_data([shape_appointment(row) for row in rows]),
        )

    except Exception:
        logger.exception("Error in get_appointments")

        return api_response(
            status_code=500,
            message="Could not retrieve the appointments",
            error_code="APPOINTMENTS_FETCH_FAILED",
            data=None,
        )


def start_of_today() -> datetime:
    """Midnight this morning in the clinic's own timezone, expressed in UTC.

    An appointment at 00:00 Monday stays on the dashboard all of Monday and
    drops off the instant Monday becomes Tuesday where the clinic actually is.
    """
    local_midnight = datetime.now(CLINIC_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return local_midnight.astimezone(timezone.utc)


def calculate_age(date_of_birth) -> int | None:
    if not isinstance(date_of_birth, datetime):
        return None

    # .date() on both sides on purpose: Mongo hands datetimes back without a
    # timezone, and subtracting one of those from an aware datetime raises.
    today = datetime.now(timezone.utc).date()
    born = date_of_birth.date()

    # the birthday has not come round yet this year, so knock a year off
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def shape_appointment(row: dict) -> dict:
    # a patient deleted out from under an appointment leaves the join empty
    patient = row.get("patient") or {}

    return {
        "_id": row["_id"],
        "scheduled_for": row.get("scheduled_for"),
        "duration_minutes": row.get("duration_minutes"),
        "status": row.get("status"),
        "reason": row.get("reason"),
        # what the WhatsApp conversation gathered before the visit
        "symptom_summary": row.get("symptom_summary"),
        "doctor_notes": row.get("doctor_notes", ""),
        "patient": {
            "_id": patient.get("_id"),
            "full_name": patient.get("full_name"),
            "preferred_name": patient.get("preferred_name"),
            "age": calculate_age(patient.get("date_of_birth")),
            "gender": patient.get("gender"),
            "whatsapp_number": patient.get("whatsapp_number"),
            "allergies": patient.get("allergies", []),
            "chronic_conditions": patient.get("chronic_conditions", []),
            "notes": patient.get("notes", ""),
        },
        "patient_history": [
            {
                "_id": visit["_id"],
                "scheduled_for": visit.get("scheduled_for"),
                "status": visit.get("status"),
                "reason": visit.get("reason"),
                "doctor_notes": visit.get("doctor_notes", ""),
                # who saw them that day, which may not be this doctor
                "seen_by": (visit.get("doctor_snapshot") or {}).get("full_name"),
            }
            for visit in row.get("patient_history", [])
        ],
    }


async def get_appointments_query(doctor_id: str, include_past: bool) -> list[dict]:
    match: dict = {"doctor_id": ObjectId(doctor_id)}

    # A day that has finished is off the dashboard, so the doctor opens the
    # screen and sees work still ahead of them rather than a growing archive.
    # include_past is what a doctor writing up yesterday evening's notes needs.
    if not include_past:
        match["scheduled_for"] = {"$gte": start_of_today()}

    pipeline = [
        {"$match": match},
        {"$sort": {"scheduled_for": 1}},
        # One round trip instead of one query per appointment. Looping and
        # calling find_one per patient would be N+1: fine for five rows, and a
        # slow morning for a doctor with a full day booked.
        {
            "$lookup": {
                "from": "patients",
                "localField": "patient_id",
                "foreignField": "_id",
                "as": "patient",
            }
        },
        # $lookup always returns an array. Without preserveNull an appointment
        # whose patient record is missing would vanish from the list entirely,
        # which is the worst way to lose a booking.
        {"$unwind": {"path": "$patient", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "appointments",
                "let": {"patient": "$patient_id", "current": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$patient_id", "$$patient"]},
                                    # the visit being looked at is not its own history
                                    {"$ne": ["$_id", "$$current"]},
                                    # completed and no_show are the ones that
                                    # already happened; booked and confirmed are
                                    # still ahead, and cancelled never occurred
                                    {
                                        "$in": [
                                            "$status",
                                            ["completed", "no_show"],
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {"$sort": {"scheduled_for": -1}},  # most recent visit first
                    {"$limit": HISTORY_LIMIT},
                    {
                        "$project": {
                            "scheduled_for": 1,
                            "status": 1,
                            "reason": 1,
                            "doctor_notes": 1,
                            "doctor_snapshot": 1,
                        }
                    },
                ],
                "as": "patient_history",
            }
        },
    ]

    # aggregate() is itself awaitable here, unlike find(), which hands back a
    # cursor directly. Awaiting it gives the cursor, then the cursor is drained.
    cursor = await get_database().appointments.aggregate(pipeline)

    return await cursor.to_list(length=None)
