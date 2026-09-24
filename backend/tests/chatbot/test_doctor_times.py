"""
Tests for the doctors the booking chat offers: the hours it quotes, the
numbered open times, and the walk-in doctors it simply tells to come in.

A fake directory stands in for the Mongo one
(app/features/whatsapp/v1/clinic_directory.py), so these need no database.

    python tests/chatbot/test_doctor_times.py
    pytest
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chatbot import classifier, directory, orchestrator  # noqa: E402
from chatbot.classifier import Classification  # noqa: E402
from chatbot.directory import Doctor  # noqa: E402
from chatbot.orchestrator import handle_message  # noqa: E402

CLINIC_TZ = timezone(timedelta(hours=5))

# Mon-Sat mornings and evenings, the week seed_schedules.py gives a doctor
WEEK = tuple(
    sorted(
        [(day, "09:00", "13:00") for day in range(6)]
        + [(day, "17:00", "20:00") for day in range(6)]
    )
)
HOURS = "Mon–Sat, 9 AM–1 PM and 5–8 PM"

ALI = Doctor("d1", "Dr. Ali Raza", "General Physician", False, WEEK)
SARA = Doctor("d2", "Dr. Sara Malik", "General Physician", True, WEEK)
HINA = Doctor("d3", "Dr. Hina Shah", "Dermatologist", False, WEEK)

MORNING = datetime(2026, 9, 23, 9, 0, tzinfo=CLINIC_TZ)  # a Wednesday
TIMES = [MORNING + timedelta(minutes=30 * step) for step in range(8)]

_counter = iter(range(10_000))


def _phone() -> str:
    return f"whatsapp:+92301{next(_counter):07d}"


def _say(phone, *messages):
    reply = None
    for message in messages:
        reply = handle_message(message, phone=phone)
    return reply


class _Directory:
    """The doctors, without a database. Registered for the with block only."""

    def __init__(self, doctors=(ALI, SARA, HINA), times=TIMES, error=None):
        self._doctors = list(doctors)
        self._times = list(times)
        self.error = error

    def _check(self):
        if self.error is not None:
            raise self.error

    def doctors(self, specialization=None):
        self._check()
        return [d for d in self._doctors if specialization in (None, d.specialization)]

    def doctor(self, doctor_id):
        self._check()
        return next((d for d in self._doctors if d.id == doctor_id), None)

    def open_times(self, doctor_id, limit):
        self._check()
        return self._times[:limit]

    def __enter__(self):
        directory.register(self)
        return self

    def __exit__(self, *exc):
        directory.register(None)


class _Model:
    """Stands in for OpenAI extraction and the model, so these run offline."""

    def __init__(self, specialization):
        self.specialization = specialization

    def __enter__(self):
        self._saved = (classifier._classifier, classifier._extractor)
        classifier.register(lambda symptoms: Classification(self.specialization, 0.9))
        classifier.register_extractor(lambda text: ["itchy_skin"])
        return self

    def __exit__(self, *exc):
        classifier._classifier, classifier._extractor = self._saved


def _to_the_doctor_step(phone, message="book an appointment with the dermatologist"):
    """Start a booking and answer up to the doctor question."""
    return _say(phone, message, "2", "Ahmed Khan", "1")


# --- offering a doctor ---------------------------------------------------


def test_one_doctor_in_a_department_is_picked_without_asking():
    with _Directory():
        reply = _to_the_doctor_step(_phone())

    assert f"Dr. Hina Shah (Dermatologist) sees patients {HOURS}" in reply.text
    assert "1. Wed 23 Sep, 9:00 AM" in reply.text, reply.text


def test_several_doctors_get_a_numbered_menu():
    with _Directory():
        reply = _to_the_doctor_step(_phone(), "book me with a general physician")

    assert "Which General Physician would you like to see?" in reply.text
    assert "1. Dr. Ali Raza, General Physician" in reply.text
    # the patient is told which one they can just walk in to
    assert "2. Dr. Sara Malik, General Physician (walk-in)" in reply.text


def test_a_general_check_up_lists_every_doctor():
    with _Directory():
        reply = _to_the_doctor_step(_phone(), "I want to book an appointment")

    assert "Which doctor would you like to see?" in reply.text
    for doctor in (ALI, SARA, HINA):
        assert doctor.name in reply.text


def test_a_department_with_no_doctor_offers_the_others():
    with _Directory(doctors=[ALI, SARA]):
        reply = _to_the_doctor_step(_phone())

    assert "We don't have a Dermatologist at the moment." in reply.text
    assert "Which General Physician" not in reply.text
    assert "1. Dr. Ali Raza" in reply.text


def test_the_model_department_chooses_the_doctor():
    with _Directory(), _Model("Dermatologist"):
        reply = _say(
            _phone(), "book an appointment", "2", "Ahmed Khan", "2", "my skin is itchy"
        )

    assert "Dr. Hina Shah (Dermatologist) sees patients" in reply.text


# --- the times -----------------------------------------------------------


def test_at_most_six_times_are_offered():
    with _Directory():
        reply = _to_the_doctor_step(_phone())

    assert "6. Wed 23 Sep, 11:30 AM" in reply.text
    assert "7. None of these" in reply.text
    assert "\n8." not in reply.text, "the menu should stop at six times"


def test_picking_a_time_sends_it_to_reception():
    phone = _phone()
    with _Directory():
        _to_the_doctor_step(phone)
        reply = handle_message("1", phone=phone)

    assert reply.collected["doctor_id"] == "d3"
    assert reply.collected["doctor_name"] == "Dr. Hina Shah"
    assert reply.collected["requested_slot"] == MORNING.isoformat()
    # a request, never a booking: the receptionist still confirms it
    assert "Wed 23 Sep, 9:00 AM with Dr. Hina Shah" in reply.text
    assert "confirm your appointment" in reply.text
    for phrase in ("you are booked", "is confirmed", "reserved", "held"):
        assert phrase not in reply.text.lower(), reply.text


def test_none_of_these_asks_for_a_time_in_words():
    phone = _phone()
    with _Directory():
        _to_the_doctor_step(phone)
        reply = handle_message("7", phone=phone)
        assert "What date and time would suit you best?" in reply.text
        reply = handle_message("Friday evening", phone=phone)

    assert reply.collected["preferred_datetime"] == "Friday evening"
    assert reply.collected["requested_slot"] == "none"
    # the doctor they chose still reaches reception
    assert reply.collected["doctor_name"] == "Dr. Hina Shah"


def test_no_open_times_falls_back_to_words():
    with _Directory(times=[]):
        reply = _to_the_doctor_step(_phone())

    assert "no open times in the next two weeks" in reply.text
    assert "What date and time would suit you best?" in reply.text


def test_a_walk_in_doctor_is_told_to_just_come_in():
    phone = _phone()
    with _Directory():
        _to_the_doctor_step(phone, "book me with a general physician")
        reply = handle_message("2", phone=phone)  # Dr. Sara Malik

    assert "first-come, first-served" in reply.text
    assert HOURS in reply.text
    assert "No appointment is needed" in reply.text
    # nothing for the receptionist to confirm
    assert reply.collected is None, reply.collected
    assert orchestrator.engine.is_active(phone) is False


# --- when the directory is not there -------------------------------------


def test_a_broken_directory_asks_for_a_time_in_words():
    with _Directory(error=RuntimeError("cluster0 unreachable")):
        reply = _to_the_doctor_step(_phone())

    assert "What date and time would suit you best?" in reply.text


def test_without_a_directory_the_chat_is_the_old_one():
    reply = _to_the_doctor_step(_phone())
    assert "What date and time would suit you best?" in reply.text


# --- asking about a doctor's schedule ------------------------------------


SCHEDULE_QUESTION = "what is the schedule of your general physician ?"


def test_asking_a_doctors_schedule_answers_it():
    with _Directory():
        reply = handle_message(SCHEDULE_QUESTION, phone=_phone())

    assert reply.source == "doctor_info", reply.source
    assert f"Dr. Ali Raza, General Physician: by appointment, {HOURS}" in reply.text
    assert "Dr. Sara Malik, General Physician: first come, first served" in reply.text
    assert "Dr. Hina Shah" not in reply.text, "only the department that was asked about"
    assert 'reply "book an appointment"' in reply.text


def test_the_same_question_mid_chat_keeps_the_chat_where_it_is():
    """The bug this was built for: the question was saved as the answer."""
    phone = _phone()
    with _Directory(times=[]):
        _to_the_doctor_step(phone)  # at "what date and time suits you?"
        reply = handle_message(SCHEDULE_QUESTION, phone=phone)
        assert "Dr. Ali Raza" in reply.text
        assert "What date and time would suit you best?" in reply.text
        reply = handle_message("Tuesday 3pm", phone=phone)

    assert reply.collected["preferred_datetime"] == "Tuesday 3pm", reply.collected


def test_the_question_is_answered_even_with_the_directory_down():
    phone = _phone()
    with _Directory(error=RuntimeError("cluster0 unreachable")):
        reply = handle_message(SCHEDULE_QUESTION, phone=phone)

    # the fixed answer, rather than "please give me a date and time"
    assert reply.source == "doctor_info", reply.source
    assert "team of experienced doctors" in reply.text


def test_booking_words_still_start_a_booking():
    with _Directory():
        reply = handle_message(
            "can I schedule an appointment with the dermatologist?", phone=_phone()
        )

    assert reply.source == "flow", reply.source
    assert "visited us before" in reply.text


def test_an_emergency_still_wins_at_the_time_menu():
    phone = _phone()
    with _Directory():
        _to_the_doctor_step(phone)
        reply = handle_message("I have severe chest pain", phone=phone)

    assert reply.source == "emergency", reply.source
    assert orchestrator.engine.is_active(phone) is False


# --- the wording ---------------------------------------------------------


def test_hours_are_described_the_way_a_person_would():
    assert directory.describe_hours(WEEK) == HOURS
    mixed = ((0, "09:00", "13:00"), (2, "09:00", "13:00"), (4, "17:30", "20:00"))
    assert directory.describe_hours(mixed) == "Mon, Wed, 9 AM–1 PM; Fri, 5:30–8 PM"


def test_a_time_reads_like_a_person_wrote_it():
    assert directory.slot_label(MORNING) == "Wed 23 Sep, 9:00 AM"
    assert directory.slot_label(MORNING.replace(hour=17, minute=30)) == (
        "Wed 23 Sep, 5:30 PM"
    )


def test_a_department_is_found_in_the_words_patients_use():
    assert directory.department_in("I need a skin specialist") == "Dermatologist"
    assert directory.department_in("can I see a child specialist?") == "Pediatrician"
    assert directory.department_in("my son needs a lady doctor") == "Gynecologist"
    # "ent" must not match inside "appointment"
    assert directory.department_in("I want an appointment") is None


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
