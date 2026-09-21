"""
Tests for the doctor portal's endpoints: saving a consultation, marking how
a visit went, a patient's medical details, and the shape of the appointment
list.

The in-memory fake in fake_mongo.py stands in for MongoDB, so these need no
database.

    python tests/app/test_doctor_portal.py
    pytest
"""

import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from pymongo.errors import DuplicateKeyError  # noqa: E402

from app.features.doctor.v1 import edit_patient_medical as medical  # noqa: E402
from app.features.doctor.v1 import get_appointments as appointments  # noqa: E402
from app.features.doctor.v1 import save_consultation as consultation  # noqa: E402
from app.features.doctor.v1 import set_appointment_status as status  # noqa: E402
from app.schemas.appointment_status_update import AppointmentStatusUpdate  # noqa: E402
from app.schemas.consultation_update import ConsultationUpdate  # noqa: E402
from app.schemas.patient_medical_update import PatientMedicalUpdate  # noqa: E402
from fake_mongo import FakeCollection, FakeDatabase  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
UTC = timezone.utc
MODULES = (medical, consultation, status)

DOCTOR_ID = ObjectId()
OTHER_DOCTOR_ID = ObjectId()
PATIENT_ID = ObjectId()

# an hour ago, so it is always today or earlier in clinic time
VISIT = {
    "_id": ObjectId(),
    "doctor_id": DOCTOR_ID,
    "patient_id": PATIENT_ID,
    "scheduled_for": datetime.now(UTC) - timedelta(hours=1),
    "duration_minutes": 30,
    "status": "booked",
    "reason": "symptoms",
    "doctor_notes": "",
}
LATER_VISIT = {
    **VISIT,
    "_id": ObjectId(),
    "scheduled_for": datetime.now(UTC) + timedelta(days=3),
}
PATIENT = {
    "_id": PATIENT_ID,
    "full_name": "Ayesha Khan",
    "whatsapp_number": "+923001234567",
    "allergies": [],
    "chronic_conditions": [],
    "blood_group": None,
    "is_active": True,
}

WRITE_UP = {
    "diagnosis": "Contact dermatitis",
    "vitals": {"bp": "120/80", "pulse": 72, "temperature": 98.6, "weight": 61.5},
    "prescriptions": [
        {
            "medicine": "Hydrocortisone cream",
            "dose": "1%",
            "frequency": "twice a day",
            "days": 7,
            "instructions": "thin layer",
        }
    ],
    "follow_up_on": date(2026, 10, 1),
    "doctor_notes": "Avoid the new soap.",
}


def _reply(coroutine):
    response = asyncio.run(coroutine)
    return response.status_code, json.loads(response.body)


def _database(visits=(VISIT,), patients=(PATIENT,), **collections):
    return FakeDatabase(
        MODULES, **{"appointments": visits, "patients": patients, **collections}
    )


def _save(appointment_id=VISIT["_id"], doctor_id=DOCTOR_ID, **changes):
    payload = {
        "doctor_id": str(doctor_id),
        "appointment_id": str(appointment_id),
        **WRITE_UP,
        **changes,
    }
    return _reply(consultation.save_consultation(payload))


def _mark(new_status, appointment_id=VISIT["_id"], doctor_id=DOCTOR_ID):
    payload = {
        "doctor_id": str(doctor_id),
        "appointment_id": str(appointment_id),
        "status": new_status,
    }
    return _reply(status.set_appointment_status(payload))


def _medical(patient_id=PATIENT_ID, doctor_id=DOCTOR_ID, **changes):
    payload = {
        "doctor_id": str(doctor_id),
        "patient_id": str(patient_id),
        "allergies": ["Penicillin"],
        "chronic_conditions": ["Asthma"],
        "blood_group": "B+",
        **changes,
    }
    return _reply(medical.edit_patient_medical(payload))


# ------------------------------------------------------------ consultation


def test_a_consultation_is_saved_with_the_notes():
    with _database() as db:
        code, body = _save()

    assert code == 200, body
    saved = db.appointments.docs[0]
    assert saved["consultation"]["diagnosis"] == "Contact dermatitis"
    assert saved["consultation"]["vitals"]["bp"] == "120/80"
    assert saved["consultation"]["prescriptions"][0]["days"] == 7
    # a day is stored as midnight UTC, and sent back as the day alone
    assert saved["consultation"]["follow_up_on"] == datetime(2026, 10, 1, tzinfo=UTC)
    assert saved["doctor_notes"] == "Avoid the new soap."
    assert saved["notes_updated_at"] is not None
    assert body["data"]["consultation"]["follow_up_on"] == "2026-10-01", body


def test_another_doctors_visit_is_not_found():
    with _database() as db:
        code, body = _save(doctor_id=OTHER_DOCTOR_ID)
    assert (code, body["error_code"]) == (404, "APPOINTMENT_NOT_FOUND"), body
    assert "consultation" not in db.appointments.docs[0]


def test_a_missed_or_cancelled_visit_has_no_consultation():
    for gone in ("no_show", "cancelled"):
        with _database(visits=[{**VISIT, "status": gone}]):
            code, body = _save()
        assert (code, body["error_code"]) == (409, "CONSULTATION_NOT_ALLOWED"), body


def test_a_completed_visit_can_still_be_written_up():
    with _database(visits=[{**VISIT, "status": "completed"}]):
        code, body = _save()
    assert code == 200, body


def test_a_malformed_id_is_a_400():
    with _database():
        code, body = _save(appointment_id="not-an-id")
    assert (code, body["error_code"]) == (400, "INVALID_APPOINTMENT_ID"), body


def test_a_database_failure_is_a_500_without_details():
    broken = FakeCollection(error=RuntimeError("connection refused to cluster0"))
    with _database(appointments=broken):
        code, body = _save()
    assert code == 500, body
    assert "cluster0" not in body["message"], body


# ------------------------------------------------------------ visit status


def test_completing_a_visit_and_undoing_it():
    with _database() as db:
        done, done_body = _mark("completed")
        assert db.appointments.docs[0]["status"] == "completed"
        undone, undone_body = _mark("booked")

    assert (done, done_body["message"]) == (200, "Visit marked as completed"), done_body
    assert (undone, undone_body["message"]) == (200, "Visit reopened"), undone_body
    assert db.appointments.docs[0]["status"] == "booked"


def test_a_later_visit_cannot_be_marked_yet():
    with _database(visits=[LATER_VISIT]) as db:
        code, body = _mark("no_show", appointment_id=LATER_VISIT["_id"])
    assert (code, body["error_code"]) == (409, "VISIT_NOT_YET"), body
    assert db.appointments.docs[0]["status"] == "booked"


def test_a_cancelled_visit_cannot_be_changed():
    with _database(visits=[{**VISIT, "status": "cancelled"}]):
        code, body = _mark("completed")
    assert (code, body["error_code"]) == (409, "APPOINTMENT_CANCELLED"), body


def test_reopening_into_a_slot_booked_since_is_refused():
    # the unique index refuses a second active visit in the same slot
    taken = FakeCollection(
        [{**VISIT, "status": "no_show"}],
        update_error=DuplicateKeyError("E11000 duplicate key"),
    )
    with _database(appointments=taken):
        code, body = _mark("booked")
    assert (code, body["error_code"]) == (409, "SLOT_TAKEN"), body


def test_another_doctors_visit_cannot_be_marked():
    with _database() as db:
        code, body = _mark("completed", doctor_id=OTHER_DOCTOR_ID)
    assert (code, body["error_code"]) == (404, "APPOINTMENT_NOT_FOUND"), body
    assert db.appointments.docs[0]["status"] == "booked"


# ---------------------------------------------------------- medical details


def test_medical_details_are_saved_for_a_patient_the_doctor_sees():
    with _database() as db:
        code, body = _medical()
    assert code == 200, body
    patient = db.patients.docs[0]
    assert patient["allergies"] == ["Penicillin"]
    assert patient["chronic_conditions"] == ["Asthma"]
    assert patient["blood_group"] == "B+"
    assert body["data"]["id"] == str(PATIENT_ID), body


def test_a_patient_the_doctor_has_never_seen_is_not_found():
    with _database() as db:
        code, body = _medical(doctor_id=OTHER_DOCTOR_ID)
    assert (code, body["error_code"]) == (404, "PATIENT_NOT_FOUND"), body
    assert db.patients.docs[0]["allergies"] == []


# ---------------------------------------------------------- request bodies


def _refuses(model, body):
    try:
        model.model_validate(body)
    except ValidationError:
        return True
    return False


def test_the_consultation_body_is_checked():
    parsed = ConsultationUpdate.model_validate(
        {"diagnosis": "  Eczema ", "vitals": {"bp": " 120/80 "}}
    )
    assert parsed.diagnosis == "Eczema" and parsed.vitals.bp == "120/80"

    assert _refuses(ConsultationUpdate, {"vitals": {"bp": "high"}})
    assert _refuses(ConsultationUpdate, {"vitals": {"pulse": 300}})
    # 37 is a fever in Celsius; the form takes Fahrenheit
    assert _refuses(ConsultationUpdate, {"vitals": {"temperature": 37}})
    assert _refuses(ConsultationUpdate, {"prescriptions": [{"medicine": " "}]})


def test_medical_lists_drop_repeats_and_blood_groups_are_real():
    parsed = PatientMedicalUpdate.model_validate(
        {"allergies": ["Penicillin", " penicillin", "Dust"], "blood_group": "O-"}
    )
    assert parsed.allergies == ["Penicillin", "Dust"], parsed.allergies
    assert _refuses(PatientMedicalUpdate, {"blood_group": "C+"})


def test_a_doctor_cannot_cancel_or_confirm_a_visit():
    AppointmentStatusUpdate.model_validate({"status": "no_show"})
    assert _refuses(AppointmentStatusUpdate, {"status": "cancelled"})
    assert _refuses(AppointmentStatusUpdate, {"status": "confirmed"})


# ------------------------------------------------------ the appointment list


def test_the_list_carries_the_consultation_and_history():
    row = {
        **VISIT,
        "consultation": {
            "diagnosis": "Eczema",
            "vitals": {"bp": "120/80"},
            "prescriptions": [{"medicine": "Cream", "days": 5}],
            "follow_up_on": datetime(2026, 10, 1),
        },
        "patient": {**PATIENT, "blood_group": "B+"},
        "patient_history": [
            {
                "_id": ObjectId(),
                "status": "completed",
                "consultation": {"diagnosis": "Rash"},
                "doctor_snapshot": {"full_name": "Dr. Sara Khan"},
            }
        ],
    }
    shaped = appointments.shape_appointment(row)

    assert shaped["consultation"]["follow_up_on"] == date(2026, 10, 1)
    assert shaped["consultation"]["vitals"] == {
        "bp": "120/80", "pulse": None, "temperature": None, "weight": None,
    }
    assert shaped["consultation"]["prescriptions"][0]["dose"] is None
    assert shaped["patient"]["blood_group"] == "B+"
    assert shaped["patient_history"][0]["diagnosis"] == "Rash"
    assert shaped["patient_history"][0]["seen_by"] == "Dr. Sara Khan"


def test_a_visit_not_yet_written_up_has_no_consultation():
    assert appointments.shape_appointment({**VISIT})["consultation"] is None


def test_every_new_route_needs_a_signed_in_doctor():
    visit_id = str(VISIT["_id"])
    responses = [
        client.put(
            f"/doctor/appointments/{visit_id}/consultation",
            json={"diagnosis": "Eczema"},
        ),
        client.patch(
            f"/doctor/appointments/{visit_id}/status", json={"status": "completed"}
        ),
        client.put(f"/doctor/patients/{PATIENT_ID}/medical", json={"allergies": []}),
    ]
    assert all(response.status_code in (401, 403) for response in responses), [
        response.status_code for response in responses
    ]


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
