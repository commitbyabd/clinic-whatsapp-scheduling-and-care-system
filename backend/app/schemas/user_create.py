from typing import Literal

from pydantic import BaseModel, EmailStr, Field, SecretStr


class UserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        max_length=254,
        description="Registered email address of the receptionist, doctor or admin",
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=64,  # bcrypt ignores anything past 72 bytes
        description="Plain-text password, hashed before storage",
    )
    role: Literal["receptionist", "doctor","admin"] = Field(
        ...,
        description="Determines dashboard access and permitted endpoints",
    )
