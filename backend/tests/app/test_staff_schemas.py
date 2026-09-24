"""
Tests for the admin's doctor forms: a doctor's specialization has to be one
of the departments the chatbot routes patients to.

    python tests/app/test_staff_schemas.py
    pytest
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pydantic import ValidationError  # noqa: E402

from app.schemas.doctor_create import DoctorCreate  # noqa: E402
from app.schemas.doctor_update import DoctorUpdate  # noqa: E402
from chatbot.classifier import SPECIALIZATIONS  # noqa: E402

DOCTOR = {
    "full_name": "Dr. Sara Khan",
    "email": "sara@clinic.com",
    "password": "correct horse",
    "specialization": "Dermatologist",
}


def _refuses(model, body):
    try:
        model.model_validate(body)
    except ValidationError:
        return True
    return False


def test_every_department_the_chatbot_knows_is_accepted():
    for department in SPECIALIZATIONS:
        DoctorCreate.model_validate({**DOCTOR, "specialization": department})


def test_a_name_the_chatbot_does_not_use_is_refused():
    # "Dermatology" never matches the chatbot's "Dermatologist", so reception
    # would never see this doctor suggested
    assert _refuses(DoctorCreate, {**DOCTOR, "specialization": "Dermatology"})
    assert _refuses(DoctorUpdate, {"specialization": "Dermatology"})


def test_an_edit_may_leave_the_specialization_out():
    update = DoctorUpdate.model_validate({"full_name": "Dr. Sara Ali"})
    assert update.specialization is None
    assert update.booking_mode is None


def test_a_doctor_takes_appointments_unless_told_otherwise():
    assert DoctorCreate.model_validate(DOCTOR).booking_mode == "appointment"
    walk_in = DoctorCreate.model_validate({**DOCTOR, "booking_mode": "walk_in"})
    assert walk_in.booking_mode == "walk_in"
    # only the two the chat knows how to answer for
    assert _refuses(DoctorCreate, {**DOCTOR, "booking_mode": "whenever"})
    assert _refuses(DoctorUpdate, {"booking_mode": "whenever"})


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}\n  {exc}\n")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} test functions passed")
    sys.exit(1 if failed else 0)
