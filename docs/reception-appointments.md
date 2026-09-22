# Reception appointments

Status: built 2026-09-22 · Area: backend + portal

## What it is

The front desk's view of visits already booked: a day at a time, across
every doctor, with the means to move a visit or cancel it. The reception
page now has two tabs, Requests (the inbox) and Appointments.

## What it does

**Appointments** (`/reception?tab=appointments`) shows one clinic day,
starting today. The previous and next day buttons, Today, and a date field
move between days. Each card shows:

- the time and length;
- the patient and their number;
- the doctor and their specialization;
- the status and the reason for the visit.

Cancelled visits stay in the list, with their reason. A visit still to come
(booked or confirmed) offers:

- **Move.** Pick the same doctor or another one, a day, and one of that
  doctor's free times. The visit goes back to booked, since the patient has
  not agreed to the new time yet.
- **Cancel.** Asks first, with an optional reason. The visit stays on
  record, and its time becomes free to book again.

**Declining** a request in the inbox also takes an optional reason now.
Both tabs refresh on their own every 30 seconds while the page is on screen,
and straight away when you come back to it.

## How it works

Endpoints, all receptionist only, in `app/features/receptionist/route.py`:

| Endpoint | File (`v1/`) | Does |
|---|---|---|
| `GET /receptionist/appointments?date=YYYY-MM-DD` | `get_day_appointments.py` | a clinic day's visits, every status, in time order |
| `PATCH /receptionist/appointments/{id}/cancel` | `cancel_appointment.py` | body `{reason?}`; booked or confirmed only |
| `PATCH /receptionist/appointments/{id}/reschedule` | `reschedule_appointment.py` | body `{doctor_id, starts_at}` |
| `PATCH /receptionist/booking-requests/{id}/decline` | `decline_booking_request.py` | now takes an optional body `{reason?}` |

- **The day list** makes two queries: the day's appointments, then their
  patients in one `$in`. It sends who and when, never clinical fields.
- **Cancel** sets `status: cancelled` with `cancel_reason`, `cancelled_by`
  and `cancelled_at`. The unique slot index ignores cancelled visits, so
  the time frees up.
- **Reschedule** checks the new time against the doctor's free slots, the
  same check as booking. It leaves the visit's own current booking out of
  that check, because an hour-long visit moved half an hour overlaps
  itself. It then updates `doctor_id`, `doctor_snapshot`, `specialization`,
  `scheduled_for`, `duration_minutes`, `status: booked`, `rescheduled_by`
  and `rescheduled_at`. The filter includes the status just read, and the
  unique index catches a booking made at the same moment.
- **Declining** stores `decline_reason` on the booking request.

Schemas: `app/schemas/appointment_change.py` (`AppointmentCancel`,
`AppointmentReschedule`) and `BookingDecline` in `booking_schedule.py`.

Portal (`components/pages/reception/`):

- `ReceptionMain.jsx`: header, the two tabs (`components/ui/TabNav.jsx`,
  shared with the doctor portal) and the toast.
- `InboxView.jsx`: the inbox, moved out of `ReceptionMain`; its decline
  dialog now has a reason field.
- `DayAppointmentsView.jsx` → `ReceptionAppointmentCard.jsx`,
  `RescheduleModal.jsx`, which reuses `SlotPicker.jsx` from scheduling.
- `ConfirmDialog` takes `children`, used for the reason fields.
- `hooks/useAutoRefresh.js`: the 30-second refresh, paused while the tab is
  hidden.
- `components/ui/StatusBadge.jsx` moved from the doctor folder, since both
  portals use it.

## Decisions

- **Nothing is deleted.** A cancelled visit stays with its reason, as the
  database rules say.
- **A moved visit is "booked" again**, even if it was confirmed: the patient
  confirmed the old time, not the new one.
- **One day at a time**, the way a front desk works. The list is small, so
  there is no paging.

## Tests

- `backend/tests/app/test_reception_appointments.py` (13):
  - the day's list: order, fields, cancelled visits kept, an empty day;
  - cancel with a reason, and refused for a visit that has happened;
  - moving within a doctor's day and to another doctor;
  - a visit not blocked by its own old time;
  - taken times refused, including a booking at the same moment;
  - decline with a reason; auth on every new route.
- `frontend/portal/src/utils/appointments.test.js`: `shiftDay` across month
  and year ends.
- Checked on 2026-09-22 against a throwaway local database, not Atlas:
  - a visit moved from 10:00 to 12:00 (its own 10:00 was not offered);
  - another cancelled with a reason, shown on its card;
  - a request declined with a reason;
  - the database checked after each.

## How to try it

Sign in as a receptionist, then open Appointments and move between days.

## Next / known gaps

- The patient is not told on WhatsApp about a move or a cancellation. That
  needs the Twilio credentials, and until then the receptionist lets them
  know.
- Declined requests and their reasons have no screen yet.
