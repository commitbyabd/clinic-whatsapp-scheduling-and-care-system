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

**users** (built): `full_name, email, password_hash, role (admin | doctor |
receptionist), specialization (doctors), is_active`

**schedules** (built, one per doctor): `doctor_id, working_hours
[{day_of_week 0-6, start_time "09:00", end_time}], slot_minutes,
blackout_dates, is_active, created_at, updated_at`

**patients** (built: created when a receptionist schedules a new patient,
read by doctor endpoints): `full_name, preferred_name, date_of_birth
(midnight UTC), gender, whatsapp_number, allergies, chronic_conditions,
blood_group, notes, is_active, created_at, updated_at`

**appointments** (built: booked by receptionists, see
[receptionist-scheduling.md](receptionist-scheduling.md); read and noted by
doctor endpoints): `doctor_id, patient_id, scheduled_for (UTC),
duration_minutes, status, reason, symptom_summary, doctor_notes,
notes_updated_at, doctor_snapshot {full_name}, specialization, request_id,
booked_by, created_at, updated_at`. Status: `booked` (a receptionist booked
it), `confirmed` (the patient confirmed; planned), `completed`, `no_show`,
`cancelled` (gives the slot back). Planned: `consultation {diagnosis, vitals
{bp, pulse, temperature, weight}, prescriptions [{medicine, dose, frequency,
days, instructions}], follow_up_on}`

**booking_requests** (built, see [booking-requests.md](booking-requests.md)):
`channel, whatsapp_number, patient_name, returning_patient, reason,
symptom_text, suggested_specialization, preferred_time_text, status (new |
scheduled | declined | cancelled), patient_id, appointment_id, handled_by,
handled_at, created_at`. Scheduling sets `scheduled` and the ids; declining
sets `declined`.

**conversation_states** (planned): replaces the chatbot's in-memory store.
`whatsapp_number (unique), flow, step, data, reprompts, updated_at`, deleted
24 hours after `updated_at`.

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
`patients (whatsapp_number)`; unique `appointments (doctor_id,
scheduled_for)` for status booked or confirmed only
(`one_active_appointment_per_slot`), which stops double booking. It is
created last, because duplicates already in the data make it fail.

Planned: `appointments (patient_id, scheduled_for)` for history; TTL indexes
on `conversation_states.updated_at` (24h) and `chat_messages.created_at`
(90d).
