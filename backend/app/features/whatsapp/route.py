from fastapi import APIRouter, Request, Response

from logging_config import logger

from .v1.webhook import reply_to_message, signature_is_valid, twiml

# No auth dependency here. Twilio cannot carry a JWT, so the signature check
# inside the handler stands in for require_role.
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

FALLBACK_REPLY = (
    "Sorry, something went wrong on our end. Please call the clinic directly "
    "and our staff will help you."
)


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    # read the whole form, not just Body: the signature covers every parameter
    # Twilio sent, so validating a subset would check the wrong thing
    form = {key: str(value) for key, value in (await request.form()).items()}

    if not signature_is_valid(request, form):
        # 403 rather than 4xx-with-body so Twilio does not retry
        return Response(status_code=403)

    body = form.get("Body", "")
    from_number = form.get("From", "")

    # status callbacks and media-only messages arrive with no text. An empty
    # <Response> means "received, send nothing".
    if not body.strip():
        logger.info("whatsapp callback with no message body, acknowledged")
        return Response(content="<Response></Response>", media_type="application/xml")

    try:
        xml = await reply_to_message(body, from_number)
    except Exception:
        # handle_message is written never to raise, so this means a real bug,
        # but the patient should still get a sentence back
        logger.exception("Error in whatsapp_webhook")
        xml = twiml(FALLBACK_REPLY)

    return Response(content=xml, media_type="application/xml")
