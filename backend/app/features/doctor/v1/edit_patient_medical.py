from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database
from app.core.response import api_response
from app.utils.object_serializer import serialize_data
from logging_config import logger


async def edit_patient_medical(payload: dict):
    doctor_id = payload.get("doctor_id")
    patient_id = payload.get("patient_id")

    if not isinstance(patient_id, str) or not ObjectId.is_valid(patient_id):
        return api_response(
            status_code=400,
            message="Patient ID is not valid",
            error_code="INVALID_PATIENT_ID",
            data=None,
        )

    if not isinstance(doctor_id, str) or not ObjectId.is_valid(doctor_id):
        return api_response(
            status_code=400,
            message="Doctor ID is not valid",
            error_code="INVALID_DOCTOR_ID",
            data=None,
        )

    try:
        # A doctor edits the patients they see, not everyone in the clinic.
        # One they have never seen answers like one that does not exist.
        if not await sees_patient_query(doctor_id, patient_id):
            return api_response(
                status_code=404,
                message="Patient not found",
                error_code="PATIENT_NOT_FOUND",
                data=None,
            )

        patient = await edit_patient_medical_query(
            patient_id,
            {
                "allergies": payload.get("allergies") or [],
                "chronic_conditions": payload.get("chronic_conditions") or [],
                "blood_group": payload.get("blood_group"),
            },
        )

        if patient is None:
            return api_response(
                status_code=404,
                message="Patient not found",
                error_code="PATIENT_NOT_FOUND",
                data=None,
            )

        return api_response(
            status_code=200,
            message="Medical details saved",
            data=serialize_data(
                {
                    "_id": patient["_id"],
                    "allergies": patient.get("allergies", []),
                    "chronic_conditions": patient.get("chronic_conditions", []),
                    "blood_group": patient.get("blood_group"),
                }
            ),
        )

    except Exception:
        logger.exception("Error in edit_patient_medical")

        return api_response(
            status_code=500,
            message="Could not save the medical details",
            error_code="MEDICAL_SAVE_FAILED",
            data=None,
        )


async def sees_patient_query(doctor_id: str, patient_id: str) -> bool:
    row = await get_database().appointments.find_one(
        {"doctor_id": ObjectId(doctor_id), "patient_id": ObjectId(patient_id)},
        {"_id": 1},
    )
    return row is not None


async def edit_patient_medical_query(patient_id: str, fields: dict) -> dict | None:
    return await get_database().patients.find_one_and_update(
        {"_id": ObjectId(patient_id)},
        {"$set": {**fields, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
