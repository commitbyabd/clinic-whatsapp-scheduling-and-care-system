# Conversation state

Status: built 2026-09-22 · Area: backend (chatbot + webhook)

## What it is

Where the booking chat remembers each patient's place: which question they
are on and what they have answered so far. It used to live in the server's
memory, so every restart dropped the chats people were halfway through. Now
it lives in MongoDB, in `conversation_states`.

## What it does

A reply like "2" only means something if the bot remembers what it asked.
Each WhatsApp number has at most one state: the flow (`appointment` or
`offer`), the step, the answers so far and how many times it re-asked. The
state is saved after every step, removed when the chat finishes or is
cancelled, and deleted by Mongo a day after the patient's last message.

## How it works

- `backend/chatbot/conversation.py` defines the `StateStore` interface, which
  is `get`, `save` and `clear`. It also has the `InMemoryStore` that the
  tests use. The chatbot still knows nothing about Mongo.
- `backend/app/features/whatsapp/v1/conversation_store.py`:
  - `MongoStateStore` implements that interface on `conversation_states`.
  - `use_mongo_store()` puts it into the chatbot's engine
    (`orchestrator.engine.store`) at startup.
- `backend/main.py` calls `use_mongo_store()` after connecting to Mongo, and
  logs "Conversation state: kept in MongoDB". If that fails, the bot keeps
  the in-memory store and says so in the log.
- `app/core/indexes.py` creates two indexes:
  - `whatsapp_number` unique: one state per number;
  - a TTL on `updated_at`, which deletes a state 24 hours after the last save
    (`STATE_TTL`).

Document: `whatsapp_number` (the bare number, like `booking_requests`),
`flow`, `step`, `data`, `reprompts`, `updated_at`.

## Decisions

- **A plain blocking client, not the app's async one.** `handle_message` runs
  on a worker thread (`run_in_threadpool` in the webhook), and the chatbot's
  code is synchronous.
- **A database fault never stops a reply.** The store logs the error type
  and behaves as if there were no chat. The patient may lose their place in
  the menu, but every message is still answered. That matters most for
  emergencies: that reply clears the state first, and it must go out.
- **Two-second timeouts.** A message can touch the state a few times, and
  Twilio gives up after 15 seconds. With the database down, measured replies
  took 2 to 4 seconds.
- **Stale or unreadable states are dropped.** A state whose step no longer
  exists (the menus changed in a later version), a broken document, or one
  older than a day reads as "no chat" and is deleted. Before this, a restart
  wiped everything, so this never came up.
- **The state still expires in code** as well as by TTL, because Mongo's TTL
  sweep runs only about once a minute.

## Tests

- `backend/tests/app/test_conversation_store.py` (8), on a small fake
  collection that hands times back without a timezone, like Mongo:
  - a whole booking chat survives a restart (a new engine on the same data);
  - the bare number is the key;
  - expired, old-menu and broken states are dropped;
  - a database fault reads as "no chat";
  - an emergency is still answered with the database down;
  - startup puts the Mongo store in place with short timeouts.
- Checked on 2026-09-22 against a throwaway local database, not Atlas:
  - two messages through the webhook, then a restart, then the rest of the
    chat: it carried on at the name question and saved a complete booking
    request;
  - the indexes were created as described;
  - with the database stopped, an emergency and a question about opening
    hours were both answered, in 2.2 and 4.2 seconds, and the log held only
    error types.

## How to try it

Start a booking on WhatsApp, restart the backend, and answer the next
question: the bot carries on. In Atlas, `cwac` → `conversation_states` shows
one document per chat in progress.

## Next / known gaps

- Two messages from the same patient arriving at the same moment can still
  overwrite each other's step. This was true of the in-memory store too.
- The server can now run more than one worker as far as chats are concerned,
  but each worker loads its own copy of the ML model.
