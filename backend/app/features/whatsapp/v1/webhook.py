"""Signature check, chatbot call, and TwiML rendering for the Twilio webhook."""

from xml.sax.saxutils import escape

from starlette.concurrency import run_in_threadpool
from twilio.request_validator import RequestValidator

from chatbot.orchestrator import handle_message
from chatbot.settings import twilio_settings
from logging_config import logger


def public_url(request) -> str:
    # Twilio signs the public URL it called. Behind a proxy we see an internal
    # one instead, so rebuild it from the forwarded headers. Set
    # TWILIO_WEBHOOK_URL if a host still gets this wrong.
    if twilio_settings.webhook_url:
        return twilio_settings.webhook_url

    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.netloc
    )
    url = f"{proto}://{host}{request.url.path}"
    return f"{url}?{request.url.query}" if request.url.query else url


def signature_is_valid(request, form: dict[str, str]) -> bool:
    if twilio_settings.skip_signature_check:
        logger.warning("Twilio signature checking is disabled, local testing only")
        return True

    # no token means we cannot verify anything, so refuse rather than accept
    if not twilio_settings.is_configured:
        logger.error("Refusing webhook request: %s", twilio_settings.explain())
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Webhook request carried no X-Twilio-Signature header")
        return False

    valid = RequestValidator(twilio_settings.auth_token).validate(
        public_url(request), form, signature
    )
    if not valid:
        logger.warning("Webhook request failed signature validation")
        logger.debug("checked against url=%s", public_url(request))

    return valid


def twiml(text: str) -> str:
    # escape() is load-bearing: an unescaped & or < produces XML Twilio cannot
    # parse, and it fails silently, so the patient just never gets a reply
    return f"<Response><Message>{escape(text)}</Message></Response>"


async def reply_to_message(body: str, from_number: str) -> str:
    # handle_message blocks for up to 10s on the OpenAI call, so keep it off
    # the event loop
    reply = await run_in_threadpool(handle_message, body, phone=from_number)

    # log the shape, never the content: the message text and the sender's
    # number together are patient health data
    logger.info("whatsapp message handled: source=%s", reply.source)

    return twiml(reply.text)
