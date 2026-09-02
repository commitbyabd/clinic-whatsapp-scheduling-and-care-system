# CWAC Backend

FastAPI + MongoDB. Serves the dashboard and public site, and answers WhatsApp
messages through the chatbot package.

Setup and run commands are in the [project README](../README.md) — this file
covers how the code is laid out.

## Layout

```
main.py              app entry: lifespan, CORS, router registration
logging_config.py    setup_logging() — call once, import the logger anywhere

app/
  core/              config (pydantic-settings), database, security,
                     response helpers, exceptions
  routers/           thin re-export of each feature's router — the seam where
                     API versioning or shared middleware would go
  features/          one directory per area: admin, auth, doctor
    <area>/route.py    endpoint definitions and their dependencies
    <area>/v1/*.py     one file per action (add_doctor, edit_receptionist, …)
  schemas/           pydantic request/response models
  db_functions/      MongoDB access
  dependencies/      require_role and other FastAPI dependencies
  utils/             object_serializer, shared helpers

chatbot/             the WhatsApp chatbot — see its __init__.py
tests/chatbot/       38 tests, no network and no API key required
```

## Conventions

**One file per action.** `features/<area>/v1/` holds a file per endpoint action
rather than a single large module, so a change to one endpoint touches one file.
`route.py` wires them to URLs and applies role dependencies.

**Roles are enforced by dependency, not by checking inside handlers.**
`require_role("doctor")` in the signature means an unauthorised request never
reaches the body. The admin routes take their target from the URL; the doctor
routes take it from the token, so a doctor cannot request somebody else's data —
there is nothing to request it with.

**`chatbot/` is not a feature.** Features have URLs; the chatbot has none. It
takes a message string and returns a reply, knowing nothing about HTTP or
Twilio, which is why its tests need no network. The Twilio webhook — pure
transport — will live in `features/whatsapp/` and call into it.
