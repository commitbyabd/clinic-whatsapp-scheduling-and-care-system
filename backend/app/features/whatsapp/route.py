from fastapi import APIRouter, Request, Response

from logging_config import logger

from .v1.webhook import reply_to_message, signature_is_valid, twiml

# No auth dependency here, unlike every other router in this app. Twilio is not
# a logged-in user and cannot carry a JWT — the signature check inside the
# handler is what takes the place of require_role.
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Sent if the chatbot itself fails unexpectedly. handle_message is written never
# to raise, so reaching this means a genuine bug — but a patient should still
# get a sentence back rather than silence.
FALLBACK_REPLY = (
    "Sorry, something went wrong on our end. Please call the clinic directly "
    "and our staff will help you."
)


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Receive one WhatsApp message from Twilio and answer it.

    The form is read whole rather than through `Body: str = Form(...)` because
    the signature covers *every* parameter Twilio sent. Validating a subset
    would check something different from what was signed.
    """
    form = {key: str(value) for key, value in (await request.form()).items()}

    if not signature_is_valid(request, form):
        # 403 with no body. Twilio will not retry a 403, which is what we want:
        # an unsigned request is not a delivery failure, it is a rejection.
        return Response(status_code=403)

    body = form.get("Body", "")
    from_number = form.get("From", "")

    if not body.strip():
        # Twilio also posts status callbacks and media-only messages, neither of
        # which carries text. Acknowledge without replying — an empty <Response>
        # tells Twilio "received, send nothing".
        logger.info("whatsapp callback with no message body, acknowledged")
        return Response(content="<Response></Response>", media_type="application/xml")

    try:
        xml = await reply_to_message(body, from_number)
    except Exception:
        logger.exception("Error in whatsapp_webhook")
        xml = twiml(FALLBACK_REPLY)

    # 200 with TwiML. Twilio reads the XML and sends the message on our behalf,
    # so there is no outbound API call to make here.
    return Response(content=xml, media_type="application/xml")
