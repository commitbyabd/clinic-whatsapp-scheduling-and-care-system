# Receptionist inbox

Status: built 2026-09-21 · Area: backend + portal

## What it is

The receptionist's first screen: the WhatsApp booking requests waiting to be
handled, newest first. Read only for now; scheduling and declining are the
next feature.

## What it does

A receptionist signs in to the portal and lands on `/reception`, which lists
every `booking_requests` document with `status: "new"`. Each card shows the
patient's name (or their number, for returning patients who were not asked),
new or returning, phone, reason, the suggested department, their symptoms in
their own words, the time they asked for, and when the request came in (clinic
time). A Refresh button reloads the list.

## How it works

Backend:

- `GET /receptionist/booking-requests?status=new&limit=50`, receptionists
  only (`app/features/receptionist/route.py`). `status` is one of new,
  scheduled, declined, cancelled; anything else is a 422.
- `app/features/receptionist/v1/get_booking_requests.py`: the query (one
  status, newest first) and `shape_booking_request`, which sends only the
  fields the card needs.
- `app/core/indexes.py`: index `(status, created_at desc)` for this query,
  created at startup.
- `app/utils/object_serializer.py`: datetimes from Mongo come back without a
  timezone, so they are now sent marked as UTC. Without this the browser
  reads them as local time and every "Received" time is off.

Portal:

- `pages/reception/Reception.jsx` → `components/pages/reception/ReceptionMain.jsx`
  (the list) → `BookingRequestCard.jsx` (one request, presentation only).
- `api/receptionist.js` (`listBookingRequests`), `hooks/useBookingRequests.js`.
- `utils/bookingRequest.js`: reason wording (matches the WhatsApp menu), the
  card title, and "Received" time in clinic time (`config/clinic.js`,
  Asia/Karachi).
- `utils/roleHome.js`: where each role lands after signing in. It's used by the
  login form, the `/` redirect and the guest guard. Before this, every role
  was sent to the admin page and receptionists saw Forbidden.
- `ClinicIdentity` takes a `label`, so the header says Reception here.

## Decisions

- **Receptionists only**, not admins: least privilege, since requests hold
  patient health data.
- **Fields are shaped by hand**, so bookkeeping fields (`handled_by`,
  `channel`) and anything added later stay off the screen.
- **No actions yet**, so there are no dead buttons; they come with scheduling.

## Tests

- `backend/tests/app/test_receptionist_inbox.py`: the query, the shaped fields,
  UTC times, an empty inbox, a database failure (500 with no details), and the
  auth guard. Uses a fake database.
- `frontend/portal/src/utils/roleHome.test.js` and `bookingRequest.test.js`.

## How to try it

Create a receptionist in the admin portal, run the backend and the portal,
sign in as the receptionist, and you land on the inbox. It needs a booking
request in the database (finish a booking on WhatsApp).

## Next / known gaps

Scheduling: pick or create the patient (matched by number), pick a free slot
from the doctor's schedule, create the appointment, and mark the request
`scheduled` (or `declined`). The list does not refresh on its own yet.
