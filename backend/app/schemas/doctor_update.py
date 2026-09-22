from pydantic import BaseModel, EmailStr, Field, field_validator

from .doctor_create import known_specialization


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = Field(None, max_length=254)
    specialization: str | None = Field(None, min_length=2, max_length=100)

    @field_validator("specialization")
    @classmethod
    def one_of_the_departments(cls, value: str | None) -> str | None:
        # left out, it stays as it is
        return value if value is None else known_specialization(value)
