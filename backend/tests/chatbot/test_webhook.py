"""
Tests for the Twilio WhatsApp webhook.

The chatbot's own behaviour is covered by the other three test files. This one
covers the transport layer, and most of it is about the security control: an
unsigned request must not reach the chatbot, and an unconfigured token must not
quietly turn the endpoint into an open door.

Signatures are computed with Twilio's own RequestValidator rather than
hand-rolled, so these tests fail if the library changes what it expects.

    python tests/chatbot/test_webhook.py
    pytest
"""

import logging
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from twilio.request_validator import RequestValidator  # noqa: E402

import app.features.whatsapp.v1.webhook as webhook  # noqa: E402
from chatbot.settings import TwilioSettings  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)

TOKEN = "test_auth_token_not_a_real_one"
URL = "https://cwac.test/whatsapp/webhook"

# Pinning webhook_url makes the signature deterministic. Without it the URL
# would depend on TestClient's host, which is exactly the fragile coupling
# public_url() exists to let you override.
CONFIGURED = TwilioSettings(
    auth_token=TOKEN, skip_signature_check=False, webhook_url=URL
)
UNCONFIGURED = TwilioSettings(
    auth_token="", skip_signature_check=False, webhook_url=URL
)
SKIPPING = TwilioSettings(
    auth_token="", skip_signature_check=True, webhook_url=URL
)


class _Settings:
    """Swap the settings webhook.py bound at import time.

    It does `from chatbot.settings import twilio_settings`, which copies the
    reference — so patching chatbot.settings would not reach it. The module
    attribute is the thing to replace.
    """

    def __init__(self, settings):
        self.settings = settings

    def __enter__(self):
        self._original = webhook.twilio_settings
        webhook.twilio_settings = self.settings
        return self

    def __exit__(self, *exc):
        webhook.twilio_settings = self._original


def _post(form, signature=None, settings=CONFIGURED):
    headers = {"X-Twilio-Signature": signature} if signature is not None else {}
    with _Settings(settings):
        return client.post("/whatsapp/webhook", data=form, headers=headers)


def _sign(form, token=TOKEN):
    return RequestValidator(token).compute_signature(URL, form)


HOURS = {"Body": "what are your timings", "From": "whatsapp:+923001234567"}


# --- the security control -----------------------------------------------


def test_valid_signature_is_accepted():
    response = _post(HOURS, _sign(HOURS))
    assert response.status_code == 200, response.text
    assert "9 AM" in response.text, response.text


def test_signature_from_the_wrong_token_is_rejected():
    response = _post(HOURS, _sign(HOURS, token="an_attackers_guess"))
    assert response.status_code == 403


def test_tampered_body_is_rejected():
    """A signature is only valid for the exact payload it was made from."""
    signature = _sign(HOURS)
    tampered = {**HOURS, "Body": "cancel every appointment"}
    assert _post(tampered, signature).status_code == 403


def test_missing_signature_header_is_rejected():
    assert _post(HOURS, signature=None).status_code == 403


def test_unconfigured_token_fails_closed():
    """No token means we cannot verify, so we refuse — never accept."""
    response = _post(HOURS, _sign(HOURS), settings=UNCONFIGURED)
    assert response.status_code == 403, (
        "an unconfigured webhook accepted a request — it must fail closed"
    )


def test_skip_flag_allows_local_testing():
    """The deliberate escape hatch, so curl works before the token arrives."""
    response = _post(HOURS, signature=None, settings=SKIPPING)
    assert response.status_code == 200
    assert "9 AM" in response.text


# --- TwiML --------------------------------------------------------------


def test_reply_is_well_formed_twiml():
    from xml.etree import ElementTree

    response = _post(HOURS, _sign(HOURS))
    root = ElementTree.fromstring(response.text)
    assert root.tag == "Response"
    assert root.find("Message") is not None
    assert response.headers["content-type"].startswith("application/xml")


def test_xml_special_characters_are_escaped():
    """Unescaped '&' produces XML Twilio cannot parse — and it fails silently."""
    original = webhook.handle_message

    def _amp(message, phone=None, symptoms=None):
        return original("what are your timings", phone=phone)

    assert webhook.twiml("Tom & Jerry <hi>") == (
        "<Response><Message>Tom &amp; Jerry &lt;hi&gt;</Message></Response>"
    )
    from xml.etree import ElementTree

    ElementTree.fromstring(webhook.twiml("A & B < C > D"))  # must not raise


def test_empty_body_is_acknowledged_without_a_reply():
    """Twilio also posts status callbacks and media-only messages."""
    form = {"Body": "", "From": "whatsapp:+923001234567"}
    response = _post(form, _sign(form))
    assert response.status_code == 200
    assert response.text == "<Response></Response>"


# --- resilience ---------------------------------------------------------


def test_chatbot_failure_still_answers_the_patient():
    """handle_message is written never to raise, but if it does, not a 500."""
    original = webhook.handle_message

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated chatbot bug")

    webhook.handle_message = _boom
    try:
        response = _post(HOURS, _sign(HOURS))
    finally:
        webhook.handle_message = original

    assert response.status_code == 200, "a patient should never see a 500"
    assert "call the clinic" in response.text.lower()


# --- privacy ------------------------------------------------------------


def test_patient_message_and_number_are_never_logged():
    """Symptoms plus a phone number are identifiable health data."""
    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = _Capture()
    root = logging.getLogger()
    root.addHandler(handler)
    previous = root.level
    root.setLevel(logging.DEBUG)

    form = {
        "Body": "I have a sharp pain in my chest since morning",
        "From": "whatsapp:+923009998877",
    }
    try:
        _post(form, _sign(form))
    finally:
        root.removeHandler(handler)
        root.setLevel(previous)

    logged = "\n".join(records)
    assert "sharp pain" not in logged, f"patient symptoms reached the logs:\n{logged}"
    assert "923009998877" not in logged, f"phone number reached the logs:\n{logged}"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}\n  {exc}\n")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} test functions passed")
    sys.exit(1 if failed else 0)
