"""
Tests for creating the TTL index that forgets idle chats.

Atlas already holds that index with its old lifetime, and Mongo refuses
create_index with the same keys and a different lifetime. Left alone, the
next startup would fail there and skip the indexes after it, so the lifetime
is changed in place with collMod. A fake stands in for the collection.

    python tests/app/test_indexes.py
    pytest
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pymongo import ASCENDING  # noqa: E402
from pymongo.errors import OperationFailure  # noqa: E402

from app.core import indexes  # noqa: E402


class _Collection:
    name = "conversation_states"

    def __init__(self, existing=None, error=None):
        # seconds of the TTL index already there, if any
        self.existing = existing
        self.error = error
        self.created = []

    async def create_index(self, field, expireAfterSeconds=None):
        if self.error is not None:
            raise self.error
        if self.existing is not None and self.existing != expireAfterSeconds:
            raise OperationFailure("index exists with different options", code=85)
        self.existing = expireAfterSeconds
        self.created.append((field, expireAfterSeconds))


class _Database:
    def __init__(self, collection):
        self.collection = collection
        self.commands = []

    async def command(self, command):
        self.commands.append(command)
        # what collMod does: change the lifetime of the index in place
        self.collection.existing = command["index"]["expireAfterSeconds"]


def _run(collection):
    database = _Database(collection)
    original = indexes.get_database
    indexes.get_database = lambda: database
    try:
        asyncio.run(indexes.ensure_ttl_index(collection, "updated_at", 7200))
    finally:
        indexes.get_database = original
    return database


def test_a_new_collection_gets_the_index():
    collection = _Collection()
    database = _run(collection)
    assert collection.created == [("updated_at", 7200)], collection.created
    assert database.commands == [], "collMod is only for an index that exists"


def test_an_index_with_the_same_lifetime_is_left_alone():
    collection = _Collection(existing=7200)
    database = _run(collection)
    assert collection.existing == 7200
    assert database.commands == []


def test_an_index_with_the_old_lifetime_is_changed_in_place():
    """The real case: a day on Atlas, two hours in the code."""
    collection = _Collection(existing=86400)
    database = _run(collection)

    assert database.commands == [
        {
            "collMod": "conversation_states",
            "index": {
                "keyPattern": {"updated_at": ASCENDING},
                "expireAfterSeconds": 7200,
            },
        }
    ], database.commands
    assert collection.existing == 7200


def test_any_other_failure_is_not_swallowed():
    collection = _Collection(error=OperationFailure("not authorized", code=13))
    try:
        _run(collection)
    except OperationFailure as exc:
        assert exc.code == 13
    else:
        raise AssertionError("an unrelated failure was hidden")


def test_the_chat_state_lifetime_is_hours_not_a_day():
    from chatbot.conversation import STATE_TTL

    assert 3600 <= STATE_TTL.total_seconds() <= 4 * 3600, STATE_TTL


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
