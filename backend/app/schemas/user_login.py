from pydantic import BaseModel, EmailStr, Field, SecretStr

class UserLogin(BaseModel):
    email: EmailStr = Field(
        # ... (ellipsis) = no default value, so the field is strictly required
        ...,
        max_length=254,  # RFC 5321 limit — also stops oversized payloads
        description="Registered email address of the receptionist or doctor",
    )
    password: SecretStr = Field(
        ...,
        description="Plain-text password, masked in logs and tracebacks",
    )
