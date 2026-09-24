# Doctors and times on WhatsApp

Status: built 2026-09-23 · Area: chatbot + backend + portal

## What it is

The booking chat used to end with "What date and time would suit you best?"
and take whatever came back as the answer — including a question. A patient
who typed "what is the schedule of your general physician ?" had that saved
as their preferred time.

Now the chat knows the clinic's doctors. It offers them by name, reads out
their hours, and lets the patient pick one of the doctor's next open times
from a numbered menu. Doctors who see patients first come, first served are
told apart: the chat gives their hours and ends, with nothing for reception
to do.

## What it does

After the reason (and symptoms, if any), the chat asks:

1. **Which doctor.** The doctors in the department the model suggested, or
   the one the patient named ("book an appointment with the dermatologist").
   One doctor is picked without asking; several become a numbered menu, with
   walk-in doctors marked. With no department, every doctor is listed.
2. **Which time.**
   - *By appointment:* "Dr. Ali Raza (General Physician) sees patients
     Mon–Sat, 9 AM–1 PM and 5–8 PM." then up to six open times as a numbered
     menu, plus "None of these", which falls back to the old free-text
     question.
   - *First come, first served:* "Dr. Sara Malik (General Physician) sees
     patients on a first-come, first-served basis: Mon–Sat, 9 AM–1 PM and
     5–8 PM. No appointment is needed, just come in during these hours." The
     chat ends there and saves nothing.

The chat also answers questions asked in the middle of it without losing the
patient's place: the question is answered and the same question is asked
again. "What is the schedule of your general physician?" lists the doctors
in that department, how each is seen and their hours.

The receptionist sees "Asked for: Wed, Sep 23, 6:00 PM, with Dr. Ali Raza"
on the request, and the Schedule dialog opens on that doctor, that day and
that time, ready to book.

## How it works

**The chatbot** (`backend/chatbot/`, still no Mongo in it):

- `directory.py` is what the chat knows about doctors: a `Doctor` (id, name,
  specialization, `walk_in`, weekly `hours`), a `Directory` provider that the
  app registers at startup, and the wording helpers `describe_hours`
  ("Mon–Sat, 9 AM–1 PM and 5–8 PM"), `slot_label` ("Wed 23 Sep, 9:00 AM") and
  `department_in` (the department a message names). Every lookup returns
  `None` when there is no directory or it failed.
- `conversation.py` gained two prepared steps, `choose_doctor` and
  `choose_time`. A `Step.prepare` hook returns a `Prepared`: a question with
  numbered choices, a `goto` (skip to another step), or a `finish` (end the
  chat with this text and save nothing), plus `answers` to record and a
  `note` to put in front of what is said next. The question and choices a
  patient saw are kept in their state, so "2" still means what they read.
- `orchestrator.py`: `_answer_aside` answers an information question during a
  chat and re-asks the current question; `_asks_doctor_schedule` catches
  "what is the schedule of your …?", which the booking rule would otherwise
  take for a booking because it contains "schedule"; `_doctors_reply` lists
  the doctors with their hours.

**The app** (`backend/app/`):

- `features/whatsapp/v1/clinic_directory.py`: `MongoDirectory`, the provider.
  Active doctors who have working hours, their booking mode, and their next
  open times over the coming 14 days.
- `features/whatsapp/v1/chatbot_setup.py`: `connect_chatbot_to_mongo()` puts
  both the state store and the directory in place at startup (called by
  `main.py`).
- `core/slots.py`: the slot maths (`working_slots`, `free_slots`,
  `slot_minutes`), moved out of the receptionist's free-slots endpoint so the
  chat offers exactly what the front desk can book.
- `save_booking_request.py` adds `requested_doctor_id`,
  `requested_doctor_name` and `requested_slot` (UTC) to the document;
  `get_booking_requests.py` sends them to the portal.
- The admin's doctor form saves `booking_mode` (`appointment` | `walk_in`) on
  the user; `get_doctors.py` leaves walk-in doctors out of reception's list.

**The portal** (`frontend/portal/src/`):

- `StaffFormModal`: a "Bookings" dropdown on the doctor form.
- Staff list: a "Walk-in" badge next to the specialization.
- `BookingRequestCard` shows the asked-for line
  (`utils/bookingRequest.js: askedForLabel`).
- `ScheduleModal` starts on the doctor, day and time the patient asked for
  (`utils/scheduling.js: pickedDoctorId, startingDay, matchingSlot`), and
  marks that doctor "(asked for)" instead of "(suggested)".

## Decisions

- **Nothing is held.** The patient asks for a time; the receptionist still
  confirms it, and the completion message says so. Holding slots would mean
  the bot books, which is the one thing it must not do.
- **Walk-in doctors send nothing to reception.** There is nothing to confirm,
  so the chat ends with the hours. They are also kept out of reception's
  doctor list, since the desk cannot book them.
- **Admin sets the mode per doctor**, on the same form as the
  specialization. Doctors saved before this take appointments.
- **Six times.** Enough to cover a day or two without a wall of text on a
  phone.
- **A question mid-chat is answered, not stored.** This is the bug the
  feature started from. The alternative — reading a date out of the
  question — would guess at what the patient meant.
- **The directory is a provider, like the state store.** The chatbot keeps
  its own vocabulary and its tests stay offline. If Mongo is unreachable the
  chat falls back to the free-text question, exactly as before.
- **The same slot maths as the front desk**, so the chat never offers a time
  the desk could not book.

## Tests

- `backend/tests/chatbot/test_doctor_times.py` (20), on a fake directory:
  one doctor picked without asking, a numbered menu with walk-ins marked,
  every doctor for a general check-up, a department with nobody in it, the
  model's department choosing the doctor, at most six times, the request that
  reaches reception, "None of these", no open times, the walk-in ending,
  a broken directory and no directory at all, the schedule question inside
  and outside a chat, booking words still starting a booking, an emergency at
  the time menu, and the wording helpers.
- `backend/tests/app/test_clinic_directory.py` (9), on a blocking fake
  collection: who is offered, walk-in from the booking mode, a doctor with no
  hours, open times in clinic time and in order, a booked slot skipped and a
  cancelled one given back.
- Updated: `test_conversation_store.py` (startup now registers the directory
  too), `test_webhook.py` (the requested fields), `test_receptionist_inbox.py`
  (they reach the desk), `test_receptionist_scheduling.py` (walk-in doctors
  left out), `test_staff_schemas.py` (booking modes).
- Portal: `utils/scheduling.test.js` and `utils/bookingRequest.test.js` cover
  the preselect and the asked-for line; 83 tests pass.
- Checked on 2026-09-23 against a throwaway local replica set, not Atlas,
  with three seeded doctors:
  - the schedule question answered with both general physicians, how each is
    seen and their hours;
  - a booking chat through the doctor menu to the time menu, a fees question
    in the middle answered with the time menu asked again, then "1" ending in
    "your request for Wed 23 Sep, 6:00 PM with Dr. Ali Raza";
  - the saved request held the doctor id, name and the slot in UTC (13:00 for
    6:00 PM), and the inbox sent them on;
  - picking the walk-in doctor ended the chat with her hours and saved
    nothing;
  - "None of these" saved the doctor with the free text and no slot;
  - reception's doctor list held the two appointment doctors only.

## How to try it

In the portal, add or edit a doctor and set **Bookings**. On WhatsApp: "book
an appointment", answer the questions, and pick a time by number. Ask "what
is the schedule of your general physician?" at any point — the answer comes
back and the chat carries on. The request then shows in the receptionist's
inbox with what was asked for.

## Next / known gaps

- The times are worked out when the doctor is picked. A patient who answers
  an hour later can still pick a time that has gone; the receptionist sees
  the clash and offers another.
- A doctor with no working hours is never offered. Run
  `scripts/seed_schedules.py` or set the hours in the doctor portal.
- Nothing tells the patient on WhatsApp once the receptionist books the time
  (it needs the Twilio credentials).
- The walk-in reply does not say how busy the clinic is, or hold a queue
  number.
