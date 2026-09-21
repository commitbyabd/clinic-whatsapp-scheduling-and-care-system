from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class PatientMedicalUpdate(BaseModel):
    # The whole list arrives each time and replaces the old one, so an empty
    # list is how the last allergy is removed.
    allergies: list[Item] = Field(default_factory=list, max_length=30)
    chronic_conditions: list[Item] = Field(default_factory=list, max_length=30)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None

    @field_validator("allergies", "chronic_conditions")
    @classmethod
    def drop_repeats(cls, items: list[str]) -> list[str]:
        # "Penicillin" and "penicillin" are the same allergy
        seen = set()
        kept = []
        for item in items:
            if item.lower() not in seen:
                seen.add(item.lower())
                kept.append(item)
        return kept
