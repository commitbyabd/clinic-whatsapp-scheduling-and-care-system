# Doctor portal

Status: built 2026-09-21 · Area: backend + portal

## What it is

The doctor's side of the staff portal, at `/doctor`. It is where a booked
visit gets its write-up, and where the doctor sets the working hours that
reception books into.

## What it does

Two tabs, kept in the URL (`?tab=appointments` or `?tab=hours`).

**Appointments.** "Upcoming" lists today and the days ahead; "Past" lists
earlier days, latest first. Visits are grouped by clinic day ("Today ·
Mon, Sep 21"). Each card shows the time, patient, age and gender, status,
reason, the patient's own words from WhatsApp, any allergies in red, and
"Written up" once a consultation exists. When no working hours are saved, a
banner explains that reception cannot book the doctor and links to the hours
tab.

Opening a visit shows:

- **Patient:** age, gender, number, allergies, long-term conditions and blood
  group. "Edit medical details" changes those three and saves them on their
  own, since they belong to the patient and not to the visit.
- **Reason for visit** and **past visits:** up to 20 completed or missed
  visits with any doctor, each with its diagnosis and notes.
- **Consultation:** diagnosis; vitals (blood pressure "120/80", pulse in bpm,
  temperature in °F, weight in kg); prescriptions (medicine, dose, how often,
  days, instructions); an optional follow-up date; notes.

The buttons depend on the visit:

| Status | Buttons |
|---|---|
| booked, today or earlier | Mark as no-show (asks first), Save, Save and complete |
| booked, a later day | Save ("can be completed on the day") |
| completed | Reopen visit, Save changes |
| no-show | Undo no-show (there is nothing to write up) |
| cancelled | Close (read only) |

**Working hours.** The length of one visit (10 to 60 minutes), then each day
Monday to Sunday with its blocks of hours. "Add hours" suggests 9–1, then
5–8, and "Copy to every day" repeats a day's blocks across the week. Days off
are dates added one by one. Mistakes show as they are typed: an end before
its start, overlapping blocks, or a block shorter than one visit. Save is
greyed out until something changes.

## How it works

Endpoints, all `require_role("doctor")`, in `app/features/doctor/route.py`.
The doctor always comes from the token, never from the URL.

| Endpoint | File (`v1/`) | Notes |
|---|---|---|
| `GET /doctor/schedule` | `get_doctor_schedule.py` | data is `[]` when none is saved |
| `PUT /doctor/schedule` | `edit_doctor_schedule.py` | replaces the whole week |
| `GET /doctor/appointments?include_past=` | `get_appointments.py` | with the patient, `consultation` and history |
| `PUT /doctor/appointments/{id}/consultation` | `save_consultation.py` | new: the whole write-up, notes included |
| `PATCH /doctor/appointments/{id}/status` | `set_appointment_status.py` | new: `completed`, `no_show`, or `booked` to undo |
| `PUT /doctor/patients/{id}/medical` | `edit_patient_medical.py` | new: allergies, conditions, blood group |

The consultation endpoint replaced `PATCH /doctor/appointments/{id}/notes`,
because the notes are part of the write-up now.

Rules the server enforces:

- **Consultation:** only on the doctor's own visit, and only when it is booked,
  confirmed or completed. A cancelled or missed visit gives 409
  `CONSULTATION_NOT_ALLOWED`, and another doctor's visit gives 404. It stores
  `consultation {diagnosis, vitals, prescriptions, follow_up_on}` plus
  `doctor_notes` and `notes_updated_at`. `follow_up_on` is stored as midnight
  UTC and sent back as the day alone.
- **Status:** completed and no-show only for a visit today or earlier in
  clinic time (409 `VISIT_NOT_YET`). A cancelled visit cannot change (409
  `APPOINTMENT_CANCELLED`). The update filters on the status just read, so a
  change made in between is never overwritten (409 `STATUS_CHANGED`).
  Reopening a missed visit whose slot has been booked again hits the
  double-booking index (409 `SLOT_TAKEN`).
- **Medical details:** only for a patient who has an appointment with this
  doctor; anyone else is 404. Lists are trimmed and repeats dropped
  (`app/schemas/patient_medical_update.py`).

Schemas are in `app/schemas/`: `consultation_update.py` (units and limits),
`appointment_status_update.py` and `patient_medical_update.py`.

Portal (`frontend/portal/src/`):

- `pages/doctor/Doctor.jsx` → `components/pages/doctor/DoctorMain.jsx`
  (tabs, toast, and the schedule, loaded once for both tabs; after a save the
  saved copy is used, so nothing is fetched again).
- `AppointmentsView.jsx` → `AppointmentCard.jsx`, `StatusBadge.jsx`.
- `ConsultationModal.jsx` (state, saving, status buttons) →
  `PatientPanel.jsx` (medical editor), `VisitHistory.jsx`,
  `ConsultationForm.jsx` (fields and prescription rows).
- `WorkingHoursView.jsx`: the week editor.
- `api/doctor.js`. `hooks/useApiResource.js` now takes a `version` that
  reloads without flashing "Loading".
- `utils/appointments.js`: statuses, grouping by clinic day, day headings.
  `utils/workingHours.js`: schedule ↔ editor, checks, payload.
  `utils/consultation.js`: visit ↔ form ↔ payload, comma lists.
  `schemas/consultation.js`: the form rules, mirroring the server.
  `schemas/validate.js` gained `validateWithPaths`, for errors like
  `prescriptions.0.medicine`.
- New shared UI: `components/ui/TextArea.jsx`, `SmallField.jsx`.
- `utils/roleHome.js`: doctors land on `/doctor`.

## Decisions

- **The write-up is one PUT.** The form sends every field each time, so
  saving twice leaves the same record. An empty string clears a field.
- **Save and complete saves first**, so the write-up is kept even if marking
  the visit fails.
- **A visit is marked only on its day or after.** A later visit cannot have
  happened, or been missed, yet.
- **Undo is "back to booked".** The doctor never sets confirmed (that is the
  patient's) or cancelled.
- **Medical details save apart from the visit**, because they belong to the
  patient.
- **Units are fixed:** °F for temperature (80 to 115, as thermometers here
  read) and kg for weight. The form says so.
- **Working hours are checked as they are typed**, including a check the
  server cannot make: a block shorter than one visit books nobody.

## Tests

- `backend/tests/app/test_doctor_portal.py` (19), on the shared fake in
  `tests/app/fake_mongo.py`:
  - saving a write-up, and its follow-up date stored as a day;
  - another doctor's visit refused; missed and cancelled visits refused;
  - completing and undoing; a later day refused; a cancelled visit refused;
  - reopening into a slot booked since; medical details for seen and unseen
    patients; the body schemas; the list's shape; auth on every new route.
- `frontend/portal/src/utils/appointments.test.js`, `workingHours.test.js`
  and `schemas/consultation.test.js` (19 in all).
- Clicked through on 2026-09-21 against a throwaway local database, not Atlas:
  - the list, the Past tab, and the no-hours banner;
  - a full write-up with a prescription, then "Save and complete", checked
    in the database; the write-up reloads when the visit is opened again;
  - editing allergies; undoing a no-show;
  - setting a week with "Copy to every day", clearing Sunday, a day off, an
    overlap refused, then a save checked in the database.

## How to try it

Run the backend and the portal, sign in as a doctor created in the admin
portal, and you land on `/doctor`. Set working hours first. Reception can then
book visits, which appear under Upcoming.

To skip typing hours, `backend/scripts/seed_schedules.py` gives every active
doctor without hours Monday to Saturday, 9 AM to 1 PM and 5 to 8 PM, in
30-minute visits. `--replace` also overwrites hours doctors already have (it
keeps their days off), and `--dry-run` only shows what would change. It
writes to the database in `backend/.env`. On 2026-09-21 it was run with
`--replace` on the shared database, and the four doctors' specializations were
renamed to the chatbot's department names (Dermatologist, Cardiologist,
Pediatrician) so reception gets the suggested doctor pre-selected.

## Next / known gaps

- The doctor sees only their own visits and cannot search for patients.
- There is no printout or WhatsApp copy of a prescription for the patient.
- Follow-up dates are recorded but nothing reminds reception to book them.
- A patient's general `notes` field is shown nowhere yet.
