"""
Turning a Twilio HTTP request into a chatbot reply, and back into TwiML.

This module is pure transport. Every decision about *what* to say lives in
`chatbot/`, which knows nothing about HTTP — so the whole conversation is
testable without a network, and this file stays small enough to audit.

Three jobs, in order:

  1. Prove the request really came from Twilio (signature).
  2. Hand the message text to the chatbot.
  3. Wrap the reply in TwiML.

Step 1 is not optional. The webhook URL ends up in a Twilio console, in a
browser history, and in whatever chat you sent it through; anyone who has it
could otherwise post fake patient messages, trigger appointment requests, and
run up your OpenAI bill. The signature is the only thing separating Twilio from
everyone else.
"""

from xml.sax.saxutils import escape

from starlette.concurrency import run_in_threadpool
from twilio.request_validator import RequestValidator

from chatbot.orchestrator import handle_message
from chatbot.settings import twilio_settings
from logging_config import logger


def public_url(request) -> str:
    """The URL Twilio signed, which is not necessarily the one we received.

    Twilio signs the exact public URL it called. Behind ngrok or Render the app
    sees an internal address — often http:// where the caller used https:// —
    and rebuilding the wrong string makes every signature fail with no clue why.
    This is the single most common reason a correctly-written webhook rejects
    real traffic.

    So: honour the proxy's forwarded headers, and allow TWILIO_WEBHOOK_URL to
    override outright when a particular host does something unusual.
    """
    if twilio_settings.webhook_url:
        return twilio_settings.webhook_url

    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.netloc
    )
    url = f"{proto}://{host}{request.url.path}"
    # Twilio signs the query string too, when there is one.
    return f"{url}?{request.url.query}" if request.url.query else url


def signature_is_valid(request, form: dict[str, str]) -> bool:
    """Whether this request carries a valid Twilio signature.

    Fails closed. An unset token means we cannot verify anything, so we reject
    rather than accept — the opposite of how the OpenAI and classifier settings
    behave, because this one is a security control rather than a feature.
    """
    if twilio_settings.skip_signature_check:
        logger.warning(
            "Twilio signature checking is DISABLED — local testing only"
        )
        return True

    if not twilio_settings.is_configured:
        logger.error(
            "Refusing webhook request: %s", twilio_settings.explain()
        )
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Webhook request carried no X-Twilio-Signature header")
        return False

    validator = RequestValidator(twilio_settings.auth_token)
    valid = validator.validate(public_url(request), form, signature)

    if not valid:
        # Deliberately vague: the URL we computed is useful to us but this line
        # may end up somewhere shared, and it is the one clue an attacker would
        # want. The reconstruction is logged at debug for when you are chasing
        # a mismatch yourself.
        logger.warning("Webhook request failed signature validation")
        logger.debug("signature was checked against url=%s", public_url(request))

    return valid


def twiml(text: str) -> str:
    """Wrap reply text in the XML Twilio expects.

    `escape()` matters more than it looks. Patients type "&" and "<" — in a
    name, in "M&S", in a time range — and unescaped they produce malformed XML.
    Twilio's failure mode there is silence: it accepts the 200, fails to parse,
    and the patient simply never receives a reply. Nothing errors anywhere.
    """
    return f"<Response><Message>{escape(text)}</Message></Response>"


async def reply_to_message(body: str, from_number: str) -> str:
    """Run one WhatsApp message through the chatbot and return TwiML.

    `handle_message` is synchronous and can block for seconds when it reaches
    the OpenAI call, so it goes to a threadpool rather than stalling the event
    loop for every other request in flight. FastAPI does this automatically for
    `def` endpoints; we are inside an `async def`, so it has to be explicit.
    """
    reply = await run_in_threadpool(handle_message, body, phone=from_number)

    # Log the SHAPE of the exchange, never its content. `body` is a patient
    # describing symptoms and `from_number` identifies them — together that is
    # health data, and application logs are the wrong place for it entirely.
    # `reply.source` is what you actually want anyway: it tells you which layer
    # answered, which is the rule-coverage and API-spend signal.
    logger.info("whatsapp message handled: source=%s", reply.source)

    return twiml(reply.text)
