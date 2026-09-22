from datetime import date

from app.core.clinic_time import clinic_day_bounds
from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def get_day_appointments(day: date):
    try:
        rows = await day_appointments_query(day)
        patients = await patients_query([row.get("patient_id") for row in rows])

        return api_response(
            status_code=200,
            message=(
                "Appointments retrieved successfully"
                if rows
                else "No appointments on this day"
            ),
            data=serialize_data(
                [shape_appointment(row, patients.get(row.get("patient_id"))) for row in rows]
            ),
        )

    except Exception:
        logger.exception("Error in get_day_appointments")

        return api_response(
            status_code=500,
            message="Could not retrieve the appointments",
            error_code="APPOINTMENTS_FETCH_FAILED",
            data=None,
        )


def shape_appointment(row: dict, patient: dict | None) -> dict:
    # who and when, for the front desk: nothing clinical
    patient = patient or {}
    return {
        "_id": row["_id"],
        "scheduled_for": row.get("scheduled_for"),
        "duration_minutes": row.get("duration_minutes"),
        "status": row.get("status"),
        "reason": row.get("reason"),
        "cancel_reason": row.get("cancel_reason"),
        "doctor": {
            "_id": row.get("doctor_id"),
            "full_name": (row.get("doctor_snapshot") or {}).get("full_name"),
            "specialization": row.get("specialization"),
        },
        "patient": {
            "_id": patient.get("_id"),
            "full_name": patient.get("full_name"),
            "whatsapp_number": patient.get("whatsapp_number"),
        },
    }


async def day_appointments_query(day: date) -> list[dict]:
    # every doctor's visits on one clinic day, cancelled ones included, so
    # the desk can see what was cancelled and why
    day_start, day_end = clinic_day_bounds(day)
    cursor = (
        get_database()
        .appointments.find({"scheduled_for": {"$gte": day_start, "$lt": day_end}})
        .sort("scheduled_for", 1)
    )
    return await cursor.to_list(length=None)


async def patients_query(patient_ids: list) -> dict:
    # one round trip for the whole day, rather than one per visit
    if not patient_ids:
        return {}
    cursor = get_database().patients.find(
        {"_id": {"$in": list(set(patient_ids))}},
        {"full_name": 1, "whatsapp_number": 1},
    )
    return {row["_id"]: row for row in await cursor.to_list(length=None)}
