from typing import Literal

from pydantic import BaseModel


class AppointmentStatusUpdate(BaseModel):
    # How the visit went. "booked" undoes a completed or no_show marked by
    # mistake; confirmed and cancelled are not the doctor's to set.
    status: Literal["booked", "completed", "no_show"]
