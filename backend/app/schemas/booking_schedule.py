from datetime import date
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class NewPatient(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., min_length=2, max_length=100)
    # both optional, so a booking is never held up by a detail the patient
    # has not given yet
    date_of_birth: date | None = None
    gender: Literal["female", "male", "other"] | None = None

    @field_validator("date_of_birth")
    @classmethod
    def not_in_the_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class BookingSchedule(BaseModel):
    doctor_id: str
    # One of the times GET /receptionist/doctors/{id}/slots sent. It must
    # carry its UTC offset, so there is no guessing which timezone it meant.
    starts_at: AwareDatetime
    # an existing patient, or the details to create one: exactly one of them
    patient_id: str | None = None
    new_patient: NewPatient | None = None

    @model_validator(mode="after")
    def exactly_one_patient(self):
        if (self.patient_id is None) == (self.new_patient is None):
            raise ValueError("Send either patient_id or new_patient")
        return self
