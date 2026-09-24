"""Connects the chatbot to MongoDB at startup: its conversation state and
its view of the doctors. The chatbot package itself never imports Mongo."""

from pymongo import MongoClient

from app.core.config import settings
from chatbot import directory, orchestrator

from .clinic_directory import MongoDirectory
from .conversation_store import MongoStateStore

# The webhook has 15 seconds before Twilio gives up, and a message can touch
# the database a few times, so a database that is down has to fail fast.
TIMEOUT_MS = 2000


def connect_chatbot_to_mongo() -> MongoClient:
    """Called once at startup; the caller closes the returned client at
    shutdown."""
    client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=TIMEOUT_MS,
        connectTimeoutMS=TIMEOUT_MS,
        socketTimeoutMS=TIMEOUT_MS,
    )
    db = client[settings.mongodb_db_name]
    orchestrator.engine.store = MongoStateStore(db.conversation_states)
    directory.register(MongoDirectory(db))
    return client
