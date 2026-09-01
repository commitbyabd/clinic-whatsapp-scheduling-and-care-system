from pydantic import BaseModel, EmailStr, Field, SecretStr


class DoctorCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=254)
    password: SecretStr = Field(..., min_length=8, max_length=64)
    specialization: str = Field(..., min_length=2, max_length=100)
