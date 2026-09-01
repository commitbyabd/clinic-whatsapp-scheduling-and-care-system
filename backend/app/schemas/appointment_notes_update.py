from pydantic import BaseModel, Field


class AppointmentNotesUpdate(BaseModel):
    # An empty string is allowed on purpose: a doctor who typed the wrong thing
    # has to be able to clear it. max_length is generous but bounded, so a stuck
    # key cannot push a megabyte of whitespace into the document.
    doctor_notes: str = Field(..., max_length=5000)
