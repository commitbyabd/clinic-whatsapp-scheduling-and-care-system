from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def edit_patient_detail(payload: dict):
    doctor_id = payload.get("doctor_id")
    appointment_id = payload.get("appointment_id")
    doctor_notes = payload.get("doctor_notes")

    try:
        # doctor_id comes off the token and appointment_id off the URL, so only
        # the second one can be anything the client felt like typing.
        if not isinstance(appointment_id, str) or not ObjectId.is_valid(
            appointment_id
        ):
            return api_response(
                status_code=400,
                message="Appointment ID is not valid",
                error_code="INVALID_APPOINTMENT_ID",
                data=None,
            )

        if not isinstance(doctor_id, str) or not ObjectId.is_valid(doctor_id):
            return api_response(
                status_code=400,
                message="Doctor ID is not valid",
                error_code="INVALID_DOCTOR_ID",
                data=None,
            )

        appointment = await edit_patient_detail_query(
            doctor_id, appointment_id, doctor_notes or ""
        )

        # Either no appointment owns that id, or one does and it belongs to a
        # different doctor. Both answer the same way on purpose: telling the
        # caller which it was would confirm another doctor's appointment exists.
        if appointment is None:
            return api_response(
                status_code=404,
                message="Appointment not found",
                error_code="APPOINTMENT_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Notes saved successfully",
            data=serialize_data(
                {
                    "_id": appointment["_id"],
                    "doctor_notes": appointment.get("doctor_notes", ""),
                    "notes_updated_at": appointment.get("notes_updated_at"),
                }
            ),
        )

    except Exception:
        logger.exception("Error in edit_patient_detail")

        return api_response(
            status_code=500,
            message="Could not save the notes",
            error_code="NOTES_SAVE_FAILED",
            data=None,
        )


async def edit_patient_detail_query(
    doctor_id: str, appointment_id: str, doctor_notes: str
) -> dict | None:
    now = datetime.now(timezone.utc)

    # doctor_id in the filter is the whole security boundary. Matching on the
    # appointment alone would let any logged-in doctor write into any other
    # doctor's consultation by guessing an id.
    return await get_database().appointments.find_one_and_update(
        {
            "_id": ObjectId(appointment_id),
            "doctor_id": ObjectId(doctor_id),
        },
        {
            "$set": {
                "doctor_notes": doctor_notes,
                # kept apart from updated_at so a later reschedule cannot make
                # it look like the clinical notes were touched
                "notes_updated_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
