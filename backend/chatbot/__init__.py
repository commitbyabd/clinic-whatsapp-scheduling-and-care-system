"""The WhatsApp chatbot: rules, scripted flow, ML classifier seam, LLM fallback.

A sibling of app/ rather than a feature inside it, because it has no URL. It
takes a message string and returns a reply, knowing nothing about HTTP,
FastAPI, Twilio or Mongo, which is why its tests need no network. The Twilio
webhook lives in app/features/whatsapp/ and calls into here.

    from chatbot.orchestrator import handle_message

    reply = handle_message(body, phone=from_number)
    reply.text     # what to send back
    reply.source   # which layer answered

    orchestrator.py         the decision chain, start here
    conversation.py         scripted question flow and per-patient state
    classifier.py           seam for the outsourced ML model
    llm_fallback.py         the OpenAI call and its safety prompt
    settings.py             config from the environment
    predefined_responses/   the rule engine
"""
