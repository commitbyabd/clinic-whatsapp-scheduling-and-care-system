from pydantic import BaseModel, EmailStr, Field


class PasswordHelpRequest(BaseModel):
    """Someone stuck at the sign-in page. The email is all they send: an
    admin reads the request and resets the password by hand."""

    email: EmailStr = Field(..., max_length=254)
