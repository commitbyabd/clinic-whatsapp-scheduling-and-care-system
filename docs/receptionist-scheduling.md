# Receptionist scheduling

Status: built 2026-09-21 · Area: backend + portal

## What it is

The step where "a receptionist confirms every booking" happens. From the
inbox, a receptionist turns a WhatsApp booking request into a real
appointment, or declines it.

## What it does

Each inbox card has **Schedule** and **Decline**.

Schedule opens a dialog in two parts:

1. **Patient.** The patients already registered under the request's WhatsApp
   number (a family can share a phone), or "New patient" (name, optional date
   of birth and gender). It starts on a best guess: the patient with the name
   that was given; else the only patient on a returning patient's number;
   else a new record for a first-timer. With several family members and no
   name, the receptionist has to pick.
2. **Doctor and time.** Active doctors who take appointments. The dialog
   starts on the doctor, day and time the patient picked on WhatsApp, marked
   "(asked for)"; with none, on the doctor whose specialization matches the
   model's suggestion, marked "(suggested)", and today
   ([whatsapp-doctor-times.md](whatsapp-doctor-times.md)). Then that
   doctor's free times for the day, in clinic time.

Book appointment saves, in one go: the patient (if new), the appointment
(`status: "booked"`), and the request as `scheduled` with `patient_id`,
`appointment_id`, `handled_by` and `handled_at`. The card leaves the inbox and
a toast confirms. Decline asks first, then marks the request `declined`.

## How it works

Endpoints, all receptionist only, in `app/features/receptionist/route.py`:

| Endpoint | File (`v1/`) | Returns |
|---|---|---|
| `GET /receptionist/booking-requests/{id}/patients` | `get_matching_patients.py` | patients on the request's number: id, full_name, date_of_birth (day only), gender |
| `POST /receptionist/booking-requests/{id}/schedule` | `schedule_booking_request.py` | 201 and the appointment |
| `PATCH /receptionist/booking-requests/{id}/decline` | `decline_booking_request.py` | the request, now declined |
| `GET /receptionist/doctors` | `get_doctors.py` | active doctors who take appointments (walk-in doctors are left out): id, full_name, specialization |
| `GET /receptionist/doctors/{id}/slots?date=YYYY-MM-DD` | `get_free_slots.py` | `{date, slot_minutes, slots: [UTC ISO]}`; the message says why there are none |

The schedule body (`app/schemas/booking_schedule.py`) is `{doctor_id,
starts_at, patient_id}` or `{doctor_id, starts_at, new_patient: {full_name,
date_of_birth?, gender?}}`, exactly one of the two. `starts_at` is a time the
slots endpoint returned, sent back unchanged; it must carry its UTC offset.

**Free slots** (`get_free_slots.py`, on the shared maths in
`app/core/slots.py`, which the WhatsApp chat uses too), worked out on every
call and never stored. `working_slots(schedule, day)` takes the doctor's blocks for that
weekday in clinic time and makes a slot every `slot_minutes` that ends by the
block's end. No schedule or a blackout day gives none, with the reason.
`free_slots()` then drops past slots and any that overlap a `booked` or
`confirmed` appointment.

**Booking** (`schedule_booking_request.py`). `run_in_transaction`
(`app/core/database.py`) runs `book()`, which:

1. re-reads the request (must be `new`) and the doctor (must be active);
2. works out the free slots again and requires `starts_at` to be one;
3. finds the patient or inserts the new one;
4. inserts the appointment;
5. marks the request, with `status: "new"` in the filter.

A `BookingRefused` raised inside undoes the transaction and becomes the 4xx
reply.

**Double booking.** The slot check covers the normal case. The unique partial
index `one_active_appointment_per_slot` on `appointments (doctor_id,
scheduled_for)`, for status booked or confirmed, stops two receptionists
taking one slot at the same moment. A cancelled visit gives its slot back.

**Clinic time.** `app/core/clinic_time.py` holds `CLINIC_TZ` (UTC+5),
`as_utc`, `clinic_time(day, "09:30")` and `clinic_day_bounds(day)`. The
doctor appointments endpoint imports `CLINIC_TZ` from there now.

Portal (`frontend/portal/src/`):

- `components/pages/reception/BookingRequestCard.jsx`: the two buttons.
- `ReceptionMain.jsx`: owns the dialogs, the decline call and the toast. It
  reloads the list whenever a dialog closes.
- `ScheduleModal.jsx`: form state and submit; `PatientPicker.jsx` and
  `SlotPicker.jsx` are its two halves. After a 409 `SLOT_NOT_FREE` it reloads
  the free times.
- `hooks/useApiResource.js`: loads one thing by key (doctors, matches,
  slots); a new key hides the old result at once.
- `utils/scheduling.js`: clinic-time formatting, today in clinic time, and
  the default patient and doctor. `schemas/scheduling.js`: new-patient rules,
  mirroring `NewPatient`.
- `components/ui/SelectField.jsx` is new, and `Modal` scrolls when its content
  is taller than the screen.

Error codes: `INVALID_ID` 400; `REQUEST_NOT_FOUND`, `DOCTOR_NOT_FOUND`,
`PATIENT_NOT_FOUND` 404; `REQUEST_ALREADY_HANDLED`, `SLOT_NOT_FREE` 409;
`SCHEDULE_FAILED`, `SLOTS_FETCH_FAILED`, `DOCTORS_FETCH_FAILED`,
`PATIENT_MATCH_FAILED`, `DECLINE_FAILED` 500.

## Decisions

- **One transaction** for patient, appointment and request, so a failure
  halfway leaves nothing behind: no orphan patient, and no appointment for a
  request still in the inbox. Transactions need a replica set; every Atlas
  cluster is one, but a plain local `mongod` is not.
- **The server checks the slot again.** The list on screen may be minutes old.
- **The number never goes in a URL.** Matching is by request id, because
  access logs keep URLs.
- **`booked` is the receptionist's booking.** `confirmed` is kept for the
  patient confirming later.
- **The appointment copies what the doctor needs:** `reason`, `symptom_text`
  as `symptom_summary`, the doctor's name (`doctor_snapshot`) and
  specialization, plus `request_id` and `booked_by`.
- **The doctor the patient asked for wins over the suggestion.** They chose
  a name and a time on WhatsApp; the model only guessed a department.
- **The suggested doctor is an exact match, ignoring case.** Admins pick
  specializations from the chatbot's own list of departments, so the names
  match (see [admin-portal.md](admin-portal.md)).
- **No medical fields for receptionists.** Matched patients show name, date
  of birth and gender only.

## Tests

- `backend/tests/app/test_receptionist_scheduling.py` (29), on an in-memory
  fake Mongo:
  - the slot maths: clinic time, blocks, days off, and past, booked and
    overlapping slots;
  - booking: all three writes, and that every write joins the transaction;
  - refusals: a taken slot, a time between slots, a booking at the same
    moment, a handled request, unknown ids, and a 500 without details;
  - decline, the body schema, and auth on every route.
- `frontend/portal/src/utils/scheduling.test.js` and
  `schemas/scheduling.test.js` (15).
- Checked by hand on 2026-09-21 against a throwaway local replica set, not
  Atlas:
  - two bookings of one slot at the same moment gave a 201 and a 409, and the
    loser's new patient was rolled back;
  - the whole flow was clicked through in the portal, desktop and phone
    width.

## How to try it

1. The doctor needs working hours. Sign in as the doctor and set them on the
   Working hours tab ([doctor-portal.md](doctor-portal.md)).
2. Finish a booking on WhatsApp, so a request is waiting.
3. Sign in as a receptionist, press Schedule, pick the patient, the doctor
   and a time, then Book appointment.
4. In Atlas you will see a new `appointments` document, a `patients` document
   if the patient was new, and the request `scheduled`.

## Next / known gaps

- **The patient is not told on WhatsApp.** Sending needs the Twilio REST API
  (Account SID and Auth Token) and, outside WhatsApp's 24-hour window, an
  approved template. Until then the receptionist tells them.
- Booked visits are listed, moved and cancelled on the Appointments tab, and
  declining takes a reason ([reception-appointments.md](reception-appointments.md)).
