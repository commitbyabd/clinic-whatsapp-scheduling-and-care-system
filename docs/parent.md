# CWAC: project context for agents

Start here. This file explains the project, how its code is organised and
where each feature is written up, so a new session can work on any part
without reading the whole repo. Read the feature file for the area you are
touching, then only the code it points to.

## The project

**CWAC (Clinic WhatsApp Automation and Care System)** is a Final Year Project
(group S26CS082, University of Central Punjab). Patients talk to a clinic on
WhatsApp: they ask questions, describe symptoms and request appointments,
without installing anything. Staff work in a web portal. The demo clinic is
called "Marigold Health", in Lahore. Its details live in
`backend/chatbot/predefined_responses/clinic.py` and
`frontend/website/src/utils/global/Constants.jsx`; change both together. The
WhatsApp number is Twilio's sandbox (+1), and the clinic's phone line is +92.

Product rules that the code enforces:

- **A receptionist confirms every booking.** The bot collects a request and
  never books, confirms or cancels anything itself.
- **The bot never diagnoses.** The ML model suggests a department, never a
  condition.
- **Patients never log in.** WhatsApp is their only channel; the portal is
  for staff (admin, receptionist, doctor).
- **Patient data never goes in logs.** Log the kind of event, never message
  text or phone numbers.
- **Secrets live only in `backend/.env`.** It is gitignored and the repo is
  public. Never commit a secret or paste one into a chat.

## Repo layout

```
backend/            FastAPI + MongoDB (Atlas). API, WhatsApp webhook, chatbot
  app/              the API: core/, features/<area>/, routers/, schemas/, utils/
  chatbot/          the WhatsApp chatbot, knows nothing about HTTP or Mongo
  tests/            chatbot/ and app/, each file runnable on its own
frontend/portal/    staff portal: React + Vite + Tailwind, port 5000
frontend/website/   public clinic website: React + Vite + CSS Modules, port 3000
docs/               this file and one file per feature
```

## Running it (Windows, from the named folder)

```
backend:   .\.venv\Scripts\python.exe -m uvicorn main:app --reload     (port 8000)
tests:     .\.venv\Scripts\python.exe tests\<chatbot|app>\<file>.py
hours:     .\.venv\Scripts\python.exe scripts\seed_schedules.py [--dry-run] [--replace]
portal:    npm run dev    npm test    npm run lint
website:   npm run dev
```

On the developer's laptop Windows Smart App Control blocks part of numpy, so
the ML model and `tests/chatbot/test_ml_classifier.py` only run on the server.

## Backend conventions

- **A feature is a folder:** `app/features/<area>/route.py` defines URLs and
  roles, `v1/<area>_dashboard.py` holds thin entry points, and
  `v1/<action>.py` does the work, returning `api_response(...)` and keeping the
  Mongo call in a separate `<action>_query` function. A shim in
  `app/routers/<area>.py` is included in `main.py`.
- **Roles by dependency:** `Depends(require_role("receptionist"))`. A route
  whose target is the caller takes the id from the token, not the URL.
- **Shape responses by hand**, listing the fields to send, so a field added to
  a document later never leaks. `serialize_data` renames `_id` to `id` and
  sends datetimes as UTC ISO strings.
- **Store UTC, show clinic time** (Pakistan, UTC+5). Helpers are in
  `app/core/clinic_time.py`.
- **Writes that must happen together** go through `run_in_transaction` in
  `app/core/database.py` (see receptionist-scheduling.md).
- **Indexes** are declared in `app/core/indexes.py` and created at startup.

## The chatbot (backend/chatbot/)

A message goes through these layers in order: emergency keywords → the
booking conversation (numbered menus, state per phone) → rule replies (hours,
location, fees) → symptoms, read by OpenAI into the model's symptom names,
then an ML model that suggests a department and offers a booking → OpenAI for
general wellness questions → a canned reply. The webhook in
`app/features/whatsapp/` is the only part that knows about Twilio or Mongo:
it registers the chat's state store and its view of the doctors at startup
(`chatbot_setup.py`), and the chatbot itself imports neither.

## Portal conventions (frontend/portal/src/)

Pages go in `pages/<area>/`, their pieces in `components/pages/<area>/`, and
shared UI in `components/ui/`. API calls live in `api/<area>.js` and return
the response envelope; `hooks/useApiResource.js` loads one of them by key,
and `hooks/useAutoRefresh.js` reloads a list every 30 seconds while it is on
screen. `Modal` and `Toast` render into `document.body`.
`ProtectedRoutes roles={[...]}` guards pages, and
`utils/roleHome.js` decides where each role lands after signing in. Design
tokens are in `variables.css`.

## Deployment

The backend runs on an office Windows server from a git clone, started with
`--workers 1` (each worker would load its own copy of the ML model; the chat
state is in Mongo, so restarts are safe). `backend/.env` and `.venv` never
come from git: they are created by hand on each machine. To update: stop
uvicorn, `git pull`, install requirements if they changed, start again.

## Working here

- Comments are short and plain, like a developer's, not long docstrings.
- The owner is a student with a frontend background who is learning
  backend. Answers should be short and plain, one step at a time.
- Commit and push only when asked.
- **Every new feature gets `docs/<feature>.md`** (template below) and a row in
  the index. Update the status list when something ships.

## Status (updated 2026-09-24)

Built: the WhatsApp chatbot end to end, the webhook on the office server,
admin portal (staff management), public website, saving booking requests,
receptionist inbox, receptionist scheduling (a request becomes an
appointment, or is declined), doctor portal (visits, consultation write-up,
medical details, working hours), chat state in Mongo (survives restarts),
reception appointments (move, cancel), staff passwords (change, reset,
and "forgot your password" as a request to the admin), doctors and their
open times offered on WhatsApp.

Next: telling the patient on WhatsApp when they are booked (needs the Twilio
credentials), deploying both frontends, demo. Phase 3 was due Sep 21, Phase 4
is due Sep 28. Dropped by choice: emailing the website's contact form (it
validates and confirms, and sends nothing), and updating the SDS.

## Feature docs

| File | Covers |
|---|---|
| [database.md](database.md) | collections, fields, agreed decisions, indexes |
| [admin-portal.md](admin-portal.md) | staff accounts: add, edit, deactivate; doctors' specializations |
| [booking-requests.md](booking-requests.md) | saving finished WhatsApp booking chats |
| [receptionist-inbox.md](receptionist-inbox.md) | the receptionist's list of new requests |
| [receptionist-scheduling.md](receptionist-scheduling.md) | free slots, matching patients, booking a request, declining |
| [doctor-portal.md](doctor-portal.md) | the doctor's visits, consultation write-up, medical details, working hours |
| [conversation-state.md](conversation-state.md) | where the booking chat keeps each patient's place, in Mongo |
| [whatsapp-doctor-times.md](whatsapp-doctor-times.md) | the chat offers doctors, their hours and open times; walk-in doctors |
| [reception-appointments.md](reception-appointments.md) | booked visits by day at the front desk: move, cancel; decline reasons |
| [staff-passwords.md](staff-passwords.md) | changing your own password, admin resets, sessions ending |
| [password-help-requests.md](password-help-requests.md) | "forgot your password": the note it leaves and the admin's Requests tab |

## Template for a feature doc

```
# <Feature>
Status: built <date> · Area: backend / portal / chatbot

## What it is
## What it does
## How it works      (files, endpoints, data)
## Decisions         (and why)
## Tests
## How to try it
## Next / known gaps
```
