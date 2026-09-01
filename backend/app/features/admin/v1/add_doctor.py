from pydantic import SecretStr

from app.core.database import get_database
from app.core.response import api_response
from app.core.security import hash_password
from app.db_functions.auth import get_user_by_email
from logging_config import logger


async def add_doctor(payload: dict):
    try:
        full_name = payload.get("full_name")
        # the schema wraps the password in SecretStr so it stays masked in logs
        password = payload.get("password")
        email = payload.get("email")
        specialization = payload.get("specialization")

        # DoctorCreate makes both of these required, but the schema belongs to
        # the route and this function no longer sees it. These two are the ones
        # that get dereferenced below, so a caller that skipped them gets a 400
        # instead of an AttributeError.
        if not isinstance(email, str) or not isinstance(password, SecretStr):
            return api_response(
                status_code=400,
                message="Email and password are required",
                error_code="MISSING_REQUIRED_FIELDS",
                data=None,
            )

        if await get_user_by_email(email):
            return api_response(
                status_code=409,
                message="A user with this email already exists",
                # success=True,
                error_code="EMAIL_TAKEN",
                data=None,
            )

        document = {
            "full_name": full_name,
            "email": email.lower(),
            "password_hash": hash_password(password.get_secret_value()),
            "specialization": specialization,
            "role": "doctor",
            "is_active": True,
        }

        result = await get_database().users.insert_one(document)

        return api_response(
            status_code=201,
            message="Doctor created successfully",
            data={"id": str(result.inserted_id)},
        )

    except Exception:
        logger.exception("Error in add_doctor")

        return api_response(
            status_code=500,
            message="Could not create the doctor",
            error_code="DOCTOR_CREATE_FAILED",
            data=None,
        )
