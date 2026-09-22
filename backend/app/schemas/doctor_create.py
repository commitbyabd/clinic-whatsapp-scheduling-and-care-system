from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from chatbot.classifier import SPECIALIZATIONS


def known_specialization(value: str) -> str:
    # The departments the chatbot sends patients to. A doctor filed under
    # the same name is the one reception sees suggested for a request.
    if value not in SPECIALIZATIONS:
        raise ValueError(
            "specialization must be one of: " + ", ".join(SPECIALIZATIONS)
        )
    return value


class DoctorCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=254)
    password: SecretStr = Field(..., min_length=8, max_length=64)
    specialization: str = Field(..., min_length=2, max_length=100)

    @field_validator("specialization")
    @classmethod
    def one_of_the_departments(cls, value: str) -> str:
        return known_specialization(value)
