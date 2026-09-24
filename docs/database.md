# Database

Status: partly built · Area: backend (MongoDB Atlas, database `cwac`)

## What it is

The data model for the whole system. Collections marked *planned* were agreed
on 2026-09-21 but have no code yet. Existing field names are used by working
endpoints, so keep them.

## How data moves

```
WhatsApp booking chat
   ▼
booking_requests      the receptionist's inbox
   ▼                  receptionist picks or creates the patient, picks a slot
appointments ──► patients (who) ──► users (which doctor) ··· schedules (free slots)
   ▼
doctor records the visit: consultation (diagnosis, vitals, prescriptions)
```

## Collections

**users** (built): `full_name, email, password_hash, password_changed_at,
role (admin | doctor | receptionist), specialization (doctors, one of the
chatbot's departments), booking_mode (doctors: appointment | walk_in, see
[whatsapp-doctor-times.md](whatsapp-doctor-times.md); missing means
appointment), is_active`. A token issued before
`password_changed_at`, or for an inactive account, is refused
([staff-passwords.md](staff-passwords.md)).

**schedules** (built, one per doctor): `doctor_id, working_hours
[{day_of_week 0-6, start_time "09:00", end_time}], slot_minutes,
blackout_dates, is_active, created_at, updated_at`

**patients** (built: created when a receptionist schedules a new patient;
allergies, chronic_conditions and blood_group are edited by doctors, see
[doctor-portal.md](doctor-portal.md)): `full_name, preferred_name,
date_of_birth (midnight UTC), gender, whatsapp_number, allergies,
chronic_conditions, blood_group (A+ … O-), notes, is_active, created_at,
updated_at`

**appointments** (built: booked by receptionists, see
[receptionist-scheduling.md](receptionist-scheduling.md); written up by
doctors, see [doctor-portal.md](doctor-portal.md)): `doctor_id, patient_id,
scheduled_for (UTC), duration_minutes, status, reason, symptom_summary,
doctor_notes, notes_updated_at, doctor_snapshot {full_name}, specialization,
request_id, booked_by, created_at, updated_at, consultation {diagnosis,
vitals {bp "120/80", pulse bpm, temperature °F, weight kg}, prescriptions
[{medicine, dose, frequency, days, instructions}], follow_up_on (midnight
UTC)}`. Status: `booked` (a receptionist booked it), `confirmed` (the patient
confirmed; planned), `completed` and `no_show` (set by the doctor, who can
undo either back to `booked`), `cancelled` (gives the slot back). Front
desk changes add `cancel_reason, cancelled_by, cancelled_at` and
`rescheduled_by, rescheduled_at`
([reception-appointments.md](reception-appointments.md)).

**booking_requests** (built, see [booking-requests.md](booking-requests.md)):
`channel, whatsapp_number, patient_name, returning_patient, reason,
symptom_text, suggested_specialization, requested_doctor_id,
requested_doctor_name, requested_slot (UTC, the open time picked in the chat),
preferred_time_text (their own words, when no open time suited), status (new |
scheduled | declined | cancelled), patient_id, appointment_id, handled_by,
handled_at, created_at`. Scheduling sets `scheduled` and the ids; declining
sets `declined` and an optional `decline_reason`.

**conversation_states** (built, see
[conversation-state.md](conversation-state.md)): each patient's place in the
booking chat. `whatsapp_number (unique, bare number), flow, step, data,
reprompts, question, choices (the menu a worked-out step showed them),
updated_at`, deleted 24 hours after `updated_at`.

**password_requests** (built, see
[password-help-requests.md](password-help-requests.md)): a staff member who
cannot sign in, waiting for an admin to reset their password. `user_id,
email, full_name, role (all a snapshot of the account), status (new |
handled), times_asked, asked_at, created_at, handled_by, handled_at`. No
password or token is ever stored here: the note is the whole feature.

**chat_messages** (planned): `whatsapp_number, patient_id, direction (in |
out), text, source, created_at`, deleted after 90 days.

## Decisions

- **booking_requests is its own collection**, so appointments only ever holds
  real, scheduled visits and a doctor's list can never show a request.
- **One WhatsApp number can belong to several patients** (a mother books for
  her children), so `patients.whatsapp_number` is not unique and the
  receptionist picks the patient.
- **Only doctors edit medical fields** (allergies, chronic conditions, blood
  group); receptionists edit name, phone and date of birth.
- **Patient history is not a collection:** it is a patient's past appointments
  with their consultations.
- **Chat history is kept 90 days**, readable by receptionists and admin only.
- **Free slots are calculated** from `schedules` minus appointments, never
  stored.
- **Nothing medical is deleted:** records are cancelled or deactivated.

## Indexes

Built (`app/core/indexes.py`): `booking_requests (status, created_at desc)`;
`patients (whatsapp_number)`; `password_requests (status, asked_at desc)`
and a unique `user_id` where the status is `new`
(`one_open_password_request_per_user`), so asking again bumps a count
instead of adding a row; `conversation_states`: unique
`whatsapp_number`, and a TTL on `updated_at` (24h); unique `appointments
(doctor_id, scheduled_for)` for status booked or confirmed only
(`one_active_appointment_per_slot`), which stops double booking. That last
one is created last, because duplicates already in the data make it fail.

Planned: `appointments (patient_id, scheduled_for)` for history; a TTL index
on `chat_messages.created_at` (90d).
