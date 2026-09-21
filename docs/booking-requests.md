# Booking requests

Status: built 2026-09-21 · Area: backend (webhook)

## What it is

The first step of the Appointment Engine. When a patient finishes the booking
chat on WhatsApp, what they said is saved to the `booking_requests`
collection for a receptionist to act on.

## What it does

The booking chat asks: visited before? (first-timers also give their name)
what for? (symptoms are read by OpenAI and the model) and when? When the chat
finishes, one document is saved with `status: "new"`:

```
channel "whatsapp", whatsapp_number "+923001234567", patient_name,
returning_patient "yes"|"no", reason "general"|"symptoms"|"followup",
symptom_text, suggested_specialization, preferred_time_text "tomorrow at 9am",
status "new", patient_id/appointment_id/handled_by/handled_at null, created_at
```

## How it works

- `backend/chatbot/orchestrator.py`: when the booking flow finishes, the reply
  carries `collected`, the patient's answers. Cancelled or handed-off chats
  carry nothing.
- `backend/app/features/whatsapp/v1/webhook.py`: `reply_to_message` saves
  `collected` before replying.
- `backend/app/features/whatsapp/v1/save_booking_request.py`: builds the
  document (`booking_request_document`) and inserts it
  (`save_booking_request_query`).

## Decisions

- **Saved in the webhook, not the chatbot**, so the chatbot still knows nothing
  about Mongo and its tests stay offline.
- **The confirmation is not sent unless the save worked.** The bot's last
  message says staff have the request, so a failed save replies "Sorry, we
  couldn't pass your request to our staff just now..." instead.
- **Only the error type is logged**, since a database error can quote the
  document.
- **The number is stored without Twilio's `whatsapp:` prefix**, so it matches
  `patients.whatsapp_number`.
- **`preferred_time_text` stays free text.** The receptionist turns it into a
  real slot.

## Tests

`backend/tests/chatbot/test_webhook.py`, "saving booking requests": a whole
chat is saved with the right fields, a failed save is not claimed as done,
other replies and cancelled chats save nothing. A fake collection is used, so
no database is needed.

## How to try it

Finish a booking on WhatsApp (to a server running this code), then look in
Atlas under `cwac` → `booking_requests`.

## Next / known gaps

Returning patients are not asked their name, so the receptionist matches them
by number. Matching and scheduling are the next feature.
