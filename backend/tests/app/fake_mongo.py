"""
An in-memory stand-in for the pymongo calls the app makes, so tests need no
database. Filters understand plain equality, $in, $ne, $gte and $lt, and
updates understand $set, $inc and $setOnInsert, which is all the app's
queries use.

Each collection records what it was asked (queries), what was inserted and
the session every write was given.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

from bson import ObjectId


def _utc(value):
    # Mongo returns datetimes without a timezone; compare them as UTC
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def matches(doc, query):
    for field, wanted in query.items():
        value = _utc(doc.get(field))
        if isinstance(wanted, dict):
            for op, operand in wanted.items():
                if op == "$in" and value not in operand:
                    return False
                if op == "$ne" and value == operand:
                    return False
                if op == "$gte" and (value is None or value < operand):
                    return False
                if op == "$lt" and (value is None or value >= operand):
                    return False
        elif value != wanted:
            return False
    return True


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, key, direction):
        self.rows.sort(key=lambda row: row.get(key), reverse=direction == -1)
        return self

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    async def to_list(self, length=None):
        return self.rows


class FakeCollection:
    def __init__(self, docs=(), error=None, insert_error=None, update_error=None):
        self.docs = [dict(doc) for doc in docs]
        self.error = error
        self.insert_error = insert_error
        self.update_error = update_error
        self.inserted = []
        self.queries = []
        self.write_sessions = []

    def _check(self, query):
        if self.error is not None:
            raise self.error
        self.queries.append(query)

    def _apply(self, doc, update):
        doc.update(update.get("$set") or {})
        for field, amount in (update.get("$inc") or {}).items():
            doc[field] = (doc.get(field) or 0) + amount
        return doc

    def _update(self, query, update, upsert=False):
        if self.update_error is not None:
            raise self.update_error
        for doc in self.docs:
            if matches(doc, query):
                return self._apply(doc, update)

        if not upsert:
            return None

        # Mongo builds the new document from the equality parts of the
        # filter, then applies the update on top
        doc = {"_id": ObjectId()}
        doc.update({field: value for field, value in query.items()
                    if not isinstance(value, dict)})
        doc.update(update.get("$setOnInsert") or {})
        self.docs.append(self._apply(doc, update))
        return doc

    async def find_one(self, query, projection=None, session=None):
        self._check(query)
        return next((dict(doc) for doc in self.docs if matches(doc, query)), None)

    def find(self, query, projection=None, session=None):
        self._check(query)
        return FakeCursor([dict(doc) for doc in self.docs if matches(doc, query)])

    async def insert_one(self, doc, session=None):
        if self.insert_error is not None:
            raise self.insert_error
        self.write_sessions.append(session)
        self.docs.append(dict(doc))
        self.inserted.append(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    async def update_one(self, query, update, session=None, upsert=False):
        self._check(query)
        self.write_sessions.append(session)
        updated = self._update(query, update, upsert)
        return SimpleNamespace(matched_count=0 if updated is None else 1)

    async def update_many(self, query, update, session=None):
        self._check(query)
        self.write_sessions.append(session)
        matched = [doc for doc in self.docs if matches(doc, query)]
        for doc in matched:
            self._apply(doc, update)
        return SimpleNamespace(matched_count=len(matched))

    async def find_one_and_update(
        self, query, update, return_document=None, session=None
    ):
        self._check(query)
        updated = self._update(query, update)
        return None if updated is None else dict(updated)


class FakeDatabase:
    """Stands in for get_database() in the given modules inside a with block.

    Collections are keyword arguments: a list of documents, or a
    FakeCollection. A collection nobody passed reads as empty.
    """

    def __init__(self, modules, **collections):
        self._modules = modules
        for name, value in collections.items():
            if not isinstance(value, FakeCollection):
                value = FakeCollection(value)
            setattr(self, name, value)

    def __getattr__(self, name):
        # only reached for a collection that was not passed in
        if name.startswith("_"):
            raise AttributeError(name)
        collection = FakeCollection()
        setattr(self, name, collection)
        return collection

    def __enter__(self):
        self._originals = [(module, module.get_database) for module in self._modules]
        for module in self._modules:
            module.get_database = lambda: self
        return self

    def __exit__(self, *exc):
        for module, original in self._originals:
            module.get_database = original
