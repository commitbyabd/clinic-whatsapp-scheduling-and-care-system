"""Keeps each patient's place in the booking chat in MongoDB, so a restart
no longer drops the conversations people are halfway through."""

from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.clinic_time import as_utc
from app.core.config import settings
from chatbot import orchestrator
from chatbot.conversation import FLOWS, ConversationState
from logging_config import logger

from .save_booking_request import WHATSAPP_PREFIX

# The webhook has 15 seconds before Twilio gives up, and a message can touch
# the state a few times, so a database that is down has to fail fast.
TIMEOUT_MS = 2000


class MongoStateStore:
    """The chatbot's StateStore, on the conversation_states collection.

    handle_message runs on a worker thread, so this uses the plain blocking
    client rather than the app's async one. A database fault is logged and
    read as "no conversation": the patient loses their place in the menu, but
    every message still gets an answer, emergencies included.
    """

    def __init__(self, collection):
        self.collection = collection

    def get(self, phone: str) -> ConversationState | None:
        try:
            row = self.collection.find_one({"whatsapp_number": _number(phone)})
        except PyMongoError as exc:
            _log_failure("read", exc)
            return None

        if row is None:
            return None

        try:
            state = ConversationState(
                phone=phone,
                flow=row["flow"],
                step=row["step"],
                data=dict(row.get("data") or {}),
                reprompts=row.get("reprompts", 0),
                updated_at=as_utc(row["updated_at"]),
            )
        except (KeyError, TypeError):
            logger.error("dropping a conversation state that could not be read")
            self.clear(phone)
            return None

        # Saved by an older version of the bot whose menus have changed since.
        # Resuming it would ask a question that no longer exists.
        if state.step not in FLOWS.get(state.flow, {}):
            logger.info("dropping a conversation state from an older menu")
            self.clear(phone)
            return None

        # the TTL index deletes old states, but only about once a minute
        if state.is_expired():
            logger.info("conversation state expired")
            self.clear(phone)
            return None

        return state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        try:
            self.collection.update_one(
                {"whatsapp_number": _number(state.phone)},
                {
                    "$set": {
                        "flow": state.flow,
                        "step": state.step,
                        "data": state.data,
                        "reprompts": state.reprompts,
                        "updated_at": state.updated_at,
                    }
                },
                upsert=True,
            )
        except PyMongoError as exc:
            _log_failure("save", exc)

    def clear(self, phone: str) -> None:
        try:
            self.collection.delete_one({"whatsapp_number": _number(phone)})
        except PyMongoError as exc:
            _log_failure("clear", exc)


def _number(phone: str) -> str:
    # stored as the bare number, like booking_requests and patients
    return phone.removeprefix(WHATSAPP_PREFIX)


def _log_failure(action: str, exc: Exception) -> None:
    # the type only: a database error can quote the document
    logger.error("Could not %s conversation state (%s)", action, type(exc).__name__)


def use_mongo_store() -> MongoClient:
    """Point the chatbot at MongoDB. Called once at startup; the caller
    closes the returned client at shutdown."""
    client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=TIMEOUT_MS,
        connectTimeoutMS=TIMEOUT_MS,
        socketTimeoutMS=TIMEOUT_MS,
    )
    collection = client[settings.mongodb_db_name].conversation_states
    orchestrator.engine.store = MongoStateStore(collection)
    return client
