"""
The WhatsApp chatbot brain: rules, scripted flow, ML classifier seam, LLM fallback.

Deliberately a sibling of `app/`, not a feature inside it. Everything in here is
transport-agnostic — it takes a message string and returns a reply, and knows
nothing about HTTP, FastAPI, Twilio, or Mongo. `app/features/whatsapp/` is where
the Twilio webhook will live; it calls into this package and does the HTTP work.

That separation is why the whole decision chain could be built and tested before
the Twilio account or the ML model existed, and it is what keeps these tests
free of network calls.

    from chatbot.orchestrator import handle_message

    reply = handle_message(body, phone=from_number)
    reply.text     # what to send back
    reply.source   # which layer answered: a rule name, "flow",
                   # "classifier", "llm", "canned", or "emergency"

Layout:
    orchestrator.py         the decision chain — start reading here
    conversation.py         scripted question flow, menus, per-patient state
    classifier.py           seam + contract for the outsourced ML model
    llm_fallback.py         the OpenAI call and its safety prompt
    settings.py             chatbot config, read from the environment
    predefined_responses/   the rule engine
"""
