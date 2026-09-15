# CWAC — Clinic WhatsApp Automation and Care System

Final Year Project · Group S26CS082 · University of Central Punjab

Moves clinic patient interaction from phone calls onto WhatsApp. Patients ask
questions, check doctor availability, and request appointments without
installing anything — a receptionist confirms every booking.

Three parts: a public clinic website, a role-based dashboard for receptionists
and doctors, and the WhatsApp channel itself via Twilio.

```
backend/            FastAPI + MongoDB — the API, and the chatbot
frontend/website/   React + Vite, CSS Modules — the public clinic website
frontend/portal/    React + Vite, Tailwind — the staff dashboard
```

The website and portal are separate apps on purpose. They share no styles, so
keeping them apart means a change to one can never break the other, and each
can be deployed on its own.

## Running it

```
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

```
cd frontend/portal
npm install
npm run dev
```

```
cd frontend/website
npm install
npm run dev
```

The portal runs on http://localhost:5000 and the website on
http://localhost:3000. The backend's `CORS_ORIGINS` has to include the portal's
address, or signing in fails.

Tests — no network calls, no API key needed:

```
cd backend
.\.venv\Scripts\python.exe tests\chatbot\test_response.py
.\.venv\Scripts\python.exe tests\chatbot\test_orchestrator.py
.\.venv\Scripts\python.exe tests\chatbot\test_conversation.py
.\.venv\Scripts\python.exe tests\chatbot\test_webhook.py
.\.venv\Scripts\python.exe tests\chatbot\test_ml_classifier.py
.\.venv\Scripts\python.exe tests\chatbot\test_symptom_extraction.py
.\.venv\Scripts\python.exe tests\chatbot\test_model_adapter.py
```

```
cd frontend/portal
npm test
```

## The chatbot

`backend/chatbot/` answers WhatsApp messages in layers, first match wins:

| | Layer | |
|---|---|---|
| 0 | emergency | checked on every message, before anything else can interpret it |
| 1 | flow | if mid-conversation, the reply is an answer to the current question |
| 2 | rules | hours, location, fees — free, instant, predictable |
| 3 | classifier | routes symptoms to one of 12 specializations (outsourced model) |
| 4 | llm | OpenAI, for general wellness questions. Never diagnoses |
| 5 | canned | a safe reply routing to staff |

Layers 3 and 4 return `None` to mean "not mine, try the next one", so a model
that is absent, disabled, unsure, or failing all behave identically — which is
why the system still runs without an OpenAI key.

Two rules the code enforces and tests assert: **the bot never diagnoses**, and
**the bot never confirms a booking** — a receptionist does.

`chatbot/` deliberately sits beside `app/` rather than inside `app/features/`.
Features have URLs; the chatbot has none — a message string goes in, a reply
comes out, and it knows nothing about HTTP, FastAPI, Twilio, or Mongo. That is
what lets it be tested without a network. Filing it under `features/` would
couple it to the transport and lose that. The reasoning is kept next to the code
in `backend/chatbot/__init__.py`.

## Status

Built and tested:

- the chatbot: rules, the scripted booking flow, and the decision chain
- the Twilio WhatsApp webhook, with signature checking
- the outsourced symptom classifier, wired in with emergency detection
- OpenAI symptom extraction: reads a patient's own words, including Roman
  Urdu, into the classifier's symptom names, with the keyword matcher as backup
- the OpenAI fallback for general wellness questions, tested with a real key
- the staff portal: admin sign-in and staff management
- the public website

99 backend tests, 23 portal tests.

Waiting on other people: the backend runs on the office server but is only
reachable inside the office network. Real WhatsApp messages need port
forwarding to that server, and the Twilio Auth Token.

Known gaps, none blocked on anyone:

- **Conversation state is in memory.** It is lost on restart, and it is why the
  backend must run with `--workers 1`. A Mongo-backed store means implementing
  three methods — `get`, `save`, `clear`.
- **The website's contact form sends nothing yet.** It validates and shows a
  confirmation, but no backend endpoint receives it.
- **Two components are missing from the Phase 2 SDS** — the ML classifier and
  the scripted question flow. Section 3.1 still describes the orchestrator as
  "predefined match → OpenAI".

## WhatsApp webhook

Twilio posts each incoming message to `POST /whatsapp/webhook`
(`backend/app/features/whatsapp/`), which calls `handle_message` and replies
with TwiML.

Every request's `X-Twilio-Signature` is checked before anything else. Without
`TWILIO_AUTH_TOKEN` the webhook refuses every request rather than trusting
them. `backend/.env.example` covers the settings, including the switch for
local testing.

`reply.collected` is populated when a booking flow finishes, carrying the
patient's answers for the Appointment Engine to turn into a `pending` record.

## Configuration

Secrets live in `backend/.env`, which is gitignored. Copy
`backend/.env.example` and fill it in — it documents every variable the app
reads. Never commit `.env`.
