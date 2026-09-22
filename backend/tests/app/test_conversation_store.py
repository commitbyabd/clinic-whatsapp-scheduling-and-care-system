"""
Tests for keeping the booking chat's state in MongoDB.

A small fake stands in for the pymongo collection, so these need no
database. It hands times back without a timezone, the way Mongo does.

    python tests/app/test_conversation_store.py
    pytest
"""

import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pymongo.errors import ServerSelectionTimeoutError  # noqa: E402

from app.features.whatsapp.v1 import conversation_store  # noqa: E402
from app.features.whatsapp.v1.conversation_store import MongoStateStore  # noqa: E402
from chatbot import orchestrator  # noqa: E402
from chatbot.conversation import (  # noqa: E402
    COMPLETION_MESSAGE,
    ConversationEngine,
    InMemoryStore,
)

PHONE = "whatsapp:+923001234567"
NUMBER = "+923001234567"


class _FakeCollection:
    """The three pymongo calls the store makes, on a dict keyed by number."""

    def __init__(self, rows=None, error=None):
        self.rows = rows or {}
        self.error = error

    def _check(self):
        if self.error is not None:
            raise self.error

    def find_one(self, query):
        self._check()
        row = self.rows.get(query["whatsapp_number"])
        # a real read is a fresh copy, never the stored object
        return copy.deepcopy(row)

    def update_one(self, query, update, upsert=False):
        self._check()
        number = query["whatsapp_number"]
        if number not in self.rows and not upsert:
            return
        fields = copy.deepcopy(update["$set"])
        # BSON keeps no timezone, so Mongo hands the time back without one
        fields["updated_at"] = fields["updated_at"].replace(tzinfo=None)
        self.rows.setdefault(number, {"whatsapp_number": number}).update(fields)

    def delete_one(self, query):
        self._check()
        self.rows.pop(query["whatsapp_number"], None)


def _row(**changes):
    return {
        "whatsapp_number": NUMBER,
        "flow": "appointment",
        "step": "ask_reason",
        "data": {"returning_patient": "yes"},
        "reprompts": 0,
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
        **changes,
    }


def test_a_booking_chat_survives_a_restart():
    collection = _FakeCollection()

    before = ConversationEngine(MongoStateStore(collection))
    before.start(PHONE, "appointment")
    before.advance(PHONE, "no")  # first visit
    before.advance(PHONE, "Ayesha Khan")

    # the server restarts: a new engine, the same database
    after = ConversationEngine(MongoStateStore(collection))
    assert after.store.get(PHONE).step == "ask_reason"
    after.advance(PHONE, "1")
    result = after.advance(PHONE, "tomorrow at 9am")

    assert result.finished and result.text == COMPLETION_MESSAGE, result
    assert result.data == {
        "returning_patient": "no",
        "name": "Ayesha Khan",
        "reason": "general",
        "preferred_datetime": "tomorrow at 9am",
    }, result.data
    # a finished chat leaves nothing behind
    assert collection.rows == {}


def test_the_state_is_stored_under_the_bare_number():
    collection = _FakeCollection()
    engine = ConversationEngine(MongoStateStore(collection))
    engine.start(PHONE, "appointment")

    assert list(collection.rows) == [NUMBER]
    row = collection.rows[NUMBER]
    assert row["flow"] == "appointment" and row["step"] == "ask_returning"
    # read back under the number the chatbot uses, prefix and all
    assert engine.store.get(PHONE).phone == PHONE


def test_an_expired_state_is_dropped():
    old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=25)
    collection = _FakeCollection({NUMBER: _row(updated_at=old)})
    assert MongoStateStore(collection).get(PHONE) is None
    assert collection.rows == {}


def test_a_state_from_an_older_menu_is_dropped():
    # a step renamed since this chat was saved would crash the engine
    collection = _FakeCollection({NUMBER: _row(step="ask_insurance")})
    assert MongoStateStore(collection).get(PHONE) is None
    assert collection.rows == {}


def test_a_broken_state_is_dropped():
    collection = _FakeCollection({NUMBER: {"whatsapp_number": NUMBER}})
    assert MongoStateStore(collection).get(PHONE) is None
    assert collection.rows == {}


def test_a_database_fault_is_read_as_no_conversation():
    store = MongoStateStore(
        _FakeCollection(error=ServerSelectionTimeoutError("cluster0 unreachable"))
    )
    # none of these may raise
    assert store.get(PHONE) is None
    store.clear(PHONE)
    engine = ConversationEngine(store)
    assert engine.start(PHONE, "appointment").step == "ask_returning"


def test_an_emergency_is_answered_even_with_the_database_down():
    # the emergency reply clears the chat first, so a failing clear must not
    # stop it going out
    down = MongoStateStore(
        _FakeCollection(error=ServerSelectionTimeoutError("cluster0 unreachable"))
    )
    original = orchestrator.engine.store
    orchestrator.engine.store = down
    try:
        reply = orchestrator.handle_message("I have severe chest pain", phone=PHONE)
    finally:
        orchestrator.engine.store = original

    assert reply.source == "emergency", reply


def test_startup_points_the_chatbot_at_mongo():
    class _FakeClient:
        def __init__(self, uri, **options):
            self.options = options

        def __getitem__(self, name):
            return SimpleNamespace(conversation_states=f"{name}.conversation_states")

        def close(self):
            pass

    original_client = conversation_store.MongoClient
    original_store = orchestrator.engine.store
    conversation_store.MongoClient = _FakeClient
    try:
        client = conversation_store.use_mongo_store()
        store = orchestrator.engine.store
    finally:
        conversation_store.MongoClient = original_client
        orchestrator.engine.store = original_store

    assert isinstance(store, MongoStateStore)
    assert store.collection.endswith(".conversation_states"), store.collection
    # fails fast rather than outlasting Twilio's 15 second limit
    assert client.options["serverSelectionTimeoutMS"] <= 5000
    assert isinstance(orchestrator.engine.store, InMemoryStore)


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
