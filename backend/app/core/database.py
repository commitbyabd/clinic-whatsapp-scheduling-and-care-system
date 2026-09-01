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
