# Project structure

One repository, one backend, one frontend. The SDS specifies "a single FastAPI
backend" and explicitly rejects microservices for a project this size, so the
split here is backend/frontend — not service-per-component.

```
Clinic Whatsapp Scheduling And Care System/     ← git repo root
├── .git/
├── .gitignore                  covers Python, secrets, venvs, node_modules
├── README.md
├── docs/
│   └── STRUCTURE.md            this file
├── frontend/                   React + Vite
│   ├── .gitignore              Vite's own, kept — frontend-specific rules
│   ├── .env.example            frontend config template
│   ├── src/  public/
│   ├── index.html
│   └── package.json
└── backend/                    FastAPI — run uvicorn from here
    ├── main.py                 app entry point
    ├── logging_config.py
    ├── requirements.txt
    ├── .env                    real secrets, gitignored
    ├── .env.example            committed template
    ├── .venv/
    ├── app/                    auth, admin, doctor, appointments
    │   ├── core/  features/  routers/
    │   ├── schemas/  db_functions/
    │   └── dependencies/  utils/
    ├── chatbot/                the WhatsApp chatbot brain
    │   ├── orchestrator.py     the decision chain — read this first
    │   ├── conversation.py     scripted question flow + per-patient state
    │   ├── classifier.py       seam for the outsourced ML model
    │   ├── llm_fallback.py     OpenAI call + safety prompt
    │   ├── settings.py         chatbot config from the environment
    │   └── predefined_responses/
    │       ├── clinic.py       per-deployment facts
    │       ├── rules.py        the intent table
    │       └── response.py     the matcher
    └── tests/
        └── chatbot/            38 tests — no network, no API key required
```

## Why `chatbot/` sits beside `app/`, not inside `app/features/`

`app/features/` holds routes — things with URLs. The chatbot has no URL. It is
domain logic: a message string goes in, a reply comes out, and it knows nothing
about HTTP, FastAPI, Twilio, or Mongo.

That is what let the entire decision chain be built and tested before the Twilio
account and the ML model existed, and it is why `tests/chatbot/` makes no network
calls and needs no API key. Filing it under `features/` would couple it to the
transport and throw that away.

The Twilio webhook is the opposite — pure transport — so it belongs in
`app/features/whatsapp/` with the other routes, and calls into `chatbot/`.

## Running it

```
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

```
cd frontend
npm run dev
```

Tests (all three should pass; expect 5/5, 16/16, 17/17):

```
cd backend
.\.venv\Scripts\python.exe tests\chatbot\test_response.py
.\.venv\Scripts\python.exe tests\chatbot\test_orchestrator.py
.\.venv\Scripts\python.exe tests\chatbot\test_conversation.py
```

## What the merge changed

Nothing inside `app/` was edited. The moves:

| Before | After |
|---|---|
| `cwacone/` | `backend/` |
| `cwacone/frontend/` | `frontend/` (lifted to a sibling) |
| `cwacone/.git/` | `.git/` (repo root is now the project root) |
| chatbot modules loose at the root | `backend/chatbot/` |
| `config.py` | `backend/chatbot/settings.py` |
| `tests/` | `backend/tests/chatbot/` |
| backend + chatbot `.gitignore` | merged into one at the repo root (Vite's own stays in `frontend/`) |
| two `requirements.txt` | one, at `backend/` |

`config.py` was renamed because `app/core/config.py` already exists and two
files called `config.py` in one project is a reading hazard.

`requirements.txt` keeps every pin from the original list byte-for-byte and in
the same order — a diff against the old file shows only additions. Nothing the
backend already depended on changed version.

`backend/README.md` was UTF-16, which is why it rendered as `c w a c - o n e`.
Converted to UTF-8; the text is unchanged.

## Still to do

1. **Rotate the two exposed credentials** — the Atlas password and `JWT_SECRET`.
   No undo on this one.
2. **Install the new dependencies** — `backend/.venv` does not have `openai` yet:
   ```
   cd backend
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. **Put a real key in `backend/.env`.** The chatbot block was appended with
   `OPENAI_API_KEY` as a placeholder. Left that way the chatbot answers from
   rules only and never calls OpenAI — it degrades, it does not crash.
4. **Delete `Webhook/`** at the repo root once step 2 passes. It holds an
   obsolete 8-line stub and a second virtualenv.
5. **Point VS Code at `backend/.venv`.** The red import squiggles were never a
   code problem — the venv used to live somewhere VS Code does not look.
6. **Commit the restructure.** Git currently shows ~63 deletions and 3 new
   directories; it records them as renames once committed, so history survives.

## When the Twilio account arrives

The webhook is the last missing piece, and it is thin because the logic is done.
It belongs in `backend/app/features/whatsapp/`, following the same convention as
your other features:

```python
from fastapi import APIRouter, Form, Request, Response
from chatbot.orchestrator import handle_message

@router.post("/webhook")
async def whatsapp_webhook(request: Request,
                           Body: str = Form(...),
                           From: str = Form(...)):
    # Validate X-Twilio-Signature before trusting anything above — without it,
    # anyone who finds this URL can post fake patient messages.
    reply = handle_message(Body, phone=From)
    return Response(
        f"<Response><Message>{escape(reply.text)}</Message></Response>",
        media_type="application/xml",
    )
```

It needs three things not yet in the repo: `python-multipart` (now in
`requirements.txt` — Twilio posts form-encoded, and FastAPI's `Form(...)` raises
at import without it), TwiML rather than JSON, and signature validation via
`twilio.request_validator.RequestValidator`.

`reply.collected` is populated when a booking flow finishes, carrying the
patient's answers for the Appointment Engine to turn into a `pending` record.

## Known gaps

- **Conversation state is in memory.** `chatbot/conversation.py` uses
  `InMemoryStore`, which loses everything on restart — on Render's free tier
  that means patients lose their place mid-booking. A Mongo-backed store means
  implementing three methods (`get`, `save`, `clear`); nothing else changes.
- **The symptom extraction step does not exist** and has no Linear issue. It is
  the OpenAI call that turns a patient's free-text description into symptom
  terms. Without it, `chatbot/classifier.py` never runs.
- **Two components are missing from the Phase 2 SDS** — the ML classifier and
  the scripted question flow. Section 3.1 still describes the orchestrator as
  "predefined match → OpenAI".
