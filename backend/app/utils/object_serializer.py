# common place to do serialization make it generic
from datetime import date, datetime
from typing import Any

from bson import ObjectId


def serialize_data(data: Any, excluded_fields: list[str] | None = None) -> Any:
    """Recursively converts a payload into JSON-safe values.

    Renames MongoDB's '_id' to 'id', turns ObjectIds and datetimes into
    strings, and removes excluded keys at every depth of the structure.

    Args:
        data: The input payload to serialize (dict, list, or scalar).
        excluded_fields: An optional list of keys to remove from dictionaries.

    Returns:
        The same structure with every value JSON-serializable.
    """
    fields_to_remove = excluded_fields or []

    # ObjectId is a BSON type with no JSON equivalent, so it becomes its hex string
    if isinstance(data, ObjectId):
        return str(data)

    # ISO 8601 is the one date format the browser's Date can parse reliably
    if isinstance(data, (datetime, date)):
        return data.isoformat()

    # Handle iterable collections (lists of documents or values)
    if isinstance(data, list):
        return [serialize_data(item, fields_to_remove) for item in data]

    # Handle dictionary instances (single documents)
    if isinstance(data, dict):
        # Built fresh rather than copied, so the caller's document is never touched
        clean_doc = {}

        for key, value in data.items():
            if key in fields_to_remove:
                continue

            # Mongo's internal '_id' is exposed to clients as 'id'
            if key == "_id":
                key = "id"

            clean_doc[key] = serialize_data(value, fields_to_remove)

        return clean_doc

    # str, int, float, bool and None are already JSON-safe
    return data
