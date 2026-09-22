from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class AppointmentCancel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # optional, but kept with the visit so the record says why
    reason: str | None = Field(None, max_length=200)


class AppointmentReschedule(BaseModel):
    # the same doctor or another one, at one of the free times
    # GET /receptionist/doctors/{id}/slots sent, with its UTC offset
    doctor_id: str
    starts_at: AwareDatetime
