from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Vitals(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # systolic over diastolic in mmHg, e.g. "120/80"
    bp: str | None = Field(None, pattern=r"^\d{2,3}/\d{2,3}$")
    pulse: int | None = Field(None, ge=20, le=250)  # beats per minute
    # Fahrenheit, the way clinic thermometers here read (98.6 is normal)
    temperature: float | None = Field(None, ge=80, le=115)
    weight: float | None = Field(None, gt=0, le=400)  # kilograms


class Prescription(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    medicine: str = Field(..., min_length=1, max_length=100)
    dose: str = Field("", max_length=50)  # "500 mg"
    frequency: str = Field("", max_length=50)  # "twice a day"
    days: int | None = Field(None, ge=1, le=365)
    instructions: str = Field("", max_length=200)  # "after meals"


class ConsultationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Everything may be blank: a doctor saves as they go, and an empty
    # string is how a field is cleared.
    diagnosis: str = Field("", max_length=500)
    vitals: Vitals = Field(default_factory=Vitals)
    prescriptions: list[Prescription] = Field(default_factory=list, max_length=20)
    follow_up_on: date | None = None
    doctor_notes: str = Field("", max_length=5000)
