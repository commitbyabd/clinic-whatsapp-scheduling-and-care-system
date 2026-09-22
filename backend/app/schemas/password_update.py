from typing import Annotated

from pydantic import BaseModel, Field, SecretStr

# The same limits as creating an account. The ceiling is because bcrypt
# ignores anything past 72 bytes.
NewPassword = Annotated[SecretStr, Field(min_length=8, max_length=64)]


class PasswordChange(BaseModel):
    """A signed-in user changing their own password."""

    current_password: SecretStr = Field(..., min_length=1, max_length=64)
    new_password: NewPassword


class PasswordReset(BaseModel):
    """An admin setting a new password for a staff member who lost theirs."""

    new_password: NewPassword
