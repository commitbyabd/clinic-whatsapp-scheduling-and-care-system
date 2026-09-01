from pydantic import BaseModel, EmailStr, Field


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = Field(None, max_length=254)
    specialization: str | None = Field(None, min_length=2, max_length=100)
