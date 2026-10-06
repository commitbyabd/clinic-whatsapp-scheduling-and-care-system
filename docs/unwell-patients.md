# Asking an unwell patient for their symptoms

Status: built 2026-10-06 · Area: chatbot

## What it is

A patient who writes "I'm not feeling well" has not said what is wrong, so
there is nothing to point them to a doctor with. The bot used to offer them
a booking straight away, and a slightly different wording ("I'm not feeling
quite well") missed the rule altogether and got a generic reply from OpenAI.

Now the bot asks what the symptoms are first, then says which department
they point to and offers the booking.

## What it does

```
Patient: I'm not feeling quite well
Bot:     We're sorry to hear that. Could you tell us your symptoms, in your
         own words? That helps us point you to the right doctor so you get
         the best care.
Patient: I have a fever, a cough and my body aches
Bot:     This sounds like something our <department> can help with.
         Would you like to book an appointment?  1. Yes  2. No
```

"Yes" starts the booking with what they described already filled in, so the
bot does not ask the reason or the symptoms again. The department is a
suggestion for reception, never a diagnosis.

- **A named symptom skips the question.** "I'm not feeling well, I have a
  fever" is offered a booking straight away, as before.
- **Unwell with a symptom the model can place** ("I feel sick, my skin is
  itchy") is offered the booking straight away too.
- **Asked once.** If the answer still names nothing, the patient gets the
  plain "Would you like to book an appointment?" rather than the question
  again.
- **Questions are answered, not swallowed.** "What are your clinic hours?"
  in the middle is answered, and the symptom question is asked again.
- **Ways out.** `cancel` leaves it; "book an appointment" starts the booking
  at once.
- **Emergencies win.** Emergency words are caught before anything else, and
  symptoms in the answer that add up to an emergency get the emergency
  reply.

## How it works

- `chatbot/predefined_responses/rules.py`: the old `feeling_unwell` rule is
  split in two, in this order.
  - `feeling_unwell` keeps the words that name a symptom (fever, cough, pain,
    headache, and so on).
  - `feeling_unwell_vague` holds the phrases that only say the patient is
    unwell: "not feeling well" and its longer forms ("not feeling quite /
    so / very well", "not feeling great"), "don't feel well" (also spelled
    without the apostrophe, and as a phone's curly one arrives, as
    "don t"), "feeling terrible", "under the weather", "unwell", "sick",
    and so on.
  - Order matters: the symptom rule comes first, so "I'm sick with a fever"
    is read as the fever.
- `chatbot/conversation.py`: a one-question flow, `triage` (`ask_triage`,
  free text), beside `appointment` and `offer`.
- `chatbot/orchestrator.py`:
  - `_offer_booking(..., ask_first=True)` asks instead of offering when no
    department could be worked out;
  - `_answer_triage` reads the answer as the symptoms and offers the booking
    through the same path as any other symptoms.
- Without a phone number (no chat state), the vague rule keeps its plain
  fixed reply.

## Decisions

- **Two rules, not one check in code.** Whether the patient named a symptom
  is a question about their wording, and the rules are where wording lives.
  A model that is down, or that reads "not feeling well" as some symptom of
  its own, then cannot make the bot ask someone who already said "fever".
- **Asked once.** A patient who cannot say more is not interrogated.
- **Nothing is saved from the question.** The answer is read, not stored as
  a booking request; reception only hears about the patient if they say yes
  and finish the booking.
- **The same offer as before.** "This sounds like something our X can help
  with" was already what a described symptom got, so this only adds the
  step before it.

## Tests

- `backend/tests/chatbot/test_response.py` (59 cases): the vague phrases,
  including "im not feeling quite well", "don't feel well" and a curly
  apostrophe, resolve to the vague rule; a named symptom beats it.
- `backend/tests/chatbot/test_conversation.py`: an unwell patient is asked,
  the answer leads to a department and an offer and saves nothing, "yes"
  books with the symptoms they gave, a vague second answer gets the plain
  offer, the longer phrasings are asked too, a named symptom or one the
  model can place is not asked, `cancel`, a question and "book an
  appointment" mid-way, an emergency in the answer, an emergency word during
  the question, and no phone number keeps the plain reply.
- Checked on 2026-10-06 through the webhook against a throwaway local
  database, not Atlas, with the real symptom model: the exact conversation
  above, an answer that names nothing, a clinic-hours question in the
  middle, and chest pain in the answer. No booking request was saved by any
  of them.

## How to try it

On WhatsApp, send "I'm not feeling well", answer with some symptoms, and
reply 1 to the offer.

## Next / known gaps

- The department comes from the model, which only sees the symptoms, so a
  vague answer can place a patient somewhere unexpected (a fever with a cough
  and aches pointed at a pulmonologist in the local check). Reception sees
  the suggestion and the patient's own words side by side and decides.
- Roman Urdu phrases for "I'm not well" are not in the vague rule.
- The chat asks in English only.
