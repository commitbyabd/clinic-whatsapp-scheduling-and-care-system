# CWAC — Clinic WhatsApp Automation and Care System

Final Year Project · Group S26CS082 · University of Central Punjab

Moves clinic patient interaction from phone calls onto WhatsApp. Patients ask
questions, check doctor availability, and request appointments without
installing anything — a receptionist confirms every booking.

Three parts: a public clinic website, a role-based dashboard for receptionists
and doctors, and the WhatsApp channel itself via Twilio.

```
backend/     FastAPI + MongoDB — the API, and the chatbot
frontend/    React + Vite — public site and dashboard
```

## Running it

```
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

```
cd frontend
npm run dev
```

Tests — no network calls, no API key needed:

```
cd backend
.\.venv\Scripts\python.exe tests\chatbot\test_response.py
.\.venv\Scripts\python.exe tests\chatbot\test_orchestrator.py
.\.venv\Scripts\python.exe tests\chatbot\test_conversation.py
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
why the system runs today with neither external component connected.

Two rules the code enforces and tests assert: **the bot never diagnoses**, and
**the bot never confirms a booking** — a receptionist does.

`chatbot/` deliberately sits beside `app/` rather than inside `app/features/`.
Features have URLs; the chatbot has none — a message string goes in, a reply
comes out, and it knows nothing about HTTP, FastAPI, Twilio, or Mongo. That is
what lets it be tested without a network. Filing it under `features/` would
couple it to the transport and lose that. The reasoning is kept next to the code
in `backend/chatbot/__init__.py`.

## Status

Built and tested: the rule engine, the decision chain, the scripted question
flow — 38 tests.

Waiting on other people: the Twilio account, and the outsourced ML classifier.
The seam for the classifier is built and tested against fakes; wiring it up is
one `register()` call.

Known gaps, none blocked on anyone:

- **The OpenAI fallback has never actually run.** The key in `.env` is a
  placeholder, so the real call and its response parsing are unverified. Needs
  only a key.
- **The symptom extraction step does not exist.** It is the OpenAI call that
  turns a patient's free-text description into symptom terms. Without it the
  classifier never receives input.
- **Conversation state is in memory** and is lost on restart, which on Render's
  free tier means patients lose their place mid-booking. A Mongo-backed store
  means implementing three methods — `get`, `save`, `clear`.
- **Two components are missing from the Phase 2 SDS** — the ML classifier and
  the scripted question flow. Section 3.1 still describes the orchestrator as
  "predefined match → OpenAI".

## When the Twilio account arrives

The webhook belongs in `backend/app/features/whatsapp/`, alongside the other
features. It is thin, because the logic is already done — read `Body` and
`From`, call `handle_message`, return TwiML:

```python
reply = handle_message(Body, phone=From)
```

Three things it needs that are not written yet: signature validation via
`twilio.request_validator.RequestValidator` (without it, anyone who finds the
URL can post fake patient messages), a TwiML rather than JSON response, and a
public URL into localhost for development. `python-multipart` is already pinned
— Twilio posts form-encoded, and FastAPI's `Form(...)` raises without it.

`reply.collected` is populated when a booking flow finishes, carrying the
patient's answers for the Appointment Engine to turn into a `pending` record.

## Configuration

Secrets live in `backend/.env`, which is gitignored. Copy
`backend/.env.example` and fill it in — it documents every variable the app
reads. Never commit `.env`.
