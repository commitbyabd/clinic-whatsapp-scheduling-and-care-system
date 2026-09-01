from collections import defaultdict
from datetime import date

from pydantic import BaseModel, Field, model_validator

# 24-hour, zero padded: "09:00", "14:30". The frontend shows AM/PM and converts
# before sending. Padded strings compare correctly with <, so every later check
# ("does this block overlap", "is this slot free") is a plain string comparison.
TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"


class WorkingHours(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0 = Monday .. 6 = Sunday
    start_time: str = Field(..., pattern=TIME_PATTERN)
    end_time: str = Field(..., pattern=TIME_PATTERN)

    @model_validator(mode="after")
    def end_must_follow_start(self):
        if self.start_time >= self.end_time:
            raise ValueError(
                f"end_time ({self.end_time}) must be later than "
                f"start_time ({self.start_time})"
            )

        return self


class DoctorScheduleUpdate(BaseModel):
    # A day may hold more than one block, so a doctor can work 09:00-13:00 and
    # 17:00-20:00 with a break between. An empty list is allowed: that is a
    # doctor who has cleared their week and takes no appointments.
    working_hours: list[WorkingHours] = Field(default_factory=list, max_length=21)
    slot_minutes: int = Field(30, ge=5, le=120)
    blackout_dates: list[date] = Field(default_factory=list)

    @model_validator(mode="after")
    def blocks_must_not_overlap(self):
        by_day: dict[int, list[WorkingHours]] = defaultdict(list)

        for block in self.working_hours:
            by_day[block.day_of_week].append(block)

        for day, blocks in by_day.items():
            # sorted by start, so only neighbours can collide
            ordered = sorted(blocks, key=lambda block: block.start_time)

            for earlier, later in zip(ordered, ordered[1:]):
                if later.start_time < earlier.end_time:
                    raise ValueError(
                        f"Overlapping blocks on day {day}: "
                        f"{earlier.start_time}-{earlier.end_time} and "
                        f"{later.start_time}-{later.end_time}"
                    )

        return self
