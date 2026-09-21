from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
class MongoDB:
    #connection to the entire atlas server cluster
    client: AsyncMongoClient | None = None
    #connection to the specific database
    db: AsyncDatabase | None = None
#=none means the type of none meaning it will have an absence of value in it 

mongo = MongoDB()
async def connect_to_mongo() -> None:
    mongo.client = AsyncMongoClient(settings.mongodb_uri)
    mongo.db = mongo.client[settings.mongodb_db_name]
    await mongo.client.admin.command("ping")
async def close_mongo_connection() -> None:
    #making sure that the client actually exists before closing the connection
    if mongo.client is not None:
        await mongo.client.close()
def get_database() -> AsyncDatabase:
    if mongo.db is None:
        raise RuntimeError("Database not initialised — is lifespan configured?")
    return mongo.db


async def run_in_transaction(work):
    # Every write work(session) makes is saved together or not at all. On a
    # write conflict the whole of work runs again, so it must be safe to
    # repeat. Transactions need a replica set, which every Atlas cluster is.
    async with get_database().client.start_session() as session:
        return await session.with_transaction(work)
