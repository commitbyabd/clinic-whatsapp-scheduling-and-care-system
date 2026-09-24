from logging_config import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.indexes import ensure_indexes
from app.features.whatsapp.v1.chatbot_setup import connect_chatbot_to_mongo
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.doctor import router as doctor_router
from app.routers.receptionist import router as receptionist_router
from app.routers.whatsapp import router as whatsapp_router
from chatbot.settings import classifier_settings, openai_settings, twilio_settings
from logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()

    # a missing index makes queries slower, not wrong, so it must not stop
    # the webhook from starting
    try:
        await ensure_indexes()
    except Exception:
        logger.exception("could not create indexes, continuing without them")

    # Each patient's place in the booking chat lives in Mongo, so a restart
    # does not drop it, and the chat reads the doctors' hours and open times
    # from there. Failing that, the chatbot keeps its in-memory store and
    # asks for a time in the patient's own words.
    state_client = None
    try:
        state_client = connect_chatbot_to_mongo()
        logger.info("Conversation state and doctors' hours: read from MongoDB")
    except Exception:
        logger.exception("chatbot not connected to MongoDB, state stays in memory")

    # Say out loud which optional pieces are actually live. Without this you
    # discover a missing key when a patient message silently takes the wrong
    # path, rather than in the first ten lines of the server log.
    for setting in (twilio_settings, openai_settings, classifier_settings):
        logger.info(setting.explain())

    # imported here rather than at the top so a missing ML package or a corrupt
    # model file cannot stop the rest of the app from starting
    try:
        from chatbot.ml.adapter import register_symptom_model

        register_symptom_model()
    except Exception:
        logger.exception("symptom model failed to load, continuing without it")

    yield  # app runs here, serving requests

    # runs once, at shutdown
    if state_client is not None:
        state_client.close()
    await close_mongo_connection()


setup_logging()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    # built-in FastAPI/Starlette component specifically designed to handle browser security headers automatically.
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


# Deliberately does not touch Mongo. Its job is to be cheap enough that an
# uptime pinger can hit it every few minutes to stop Render's free tier
# sleeping — a cold start takes longer than Twilio's webhook timeout, so the
# first patient message after an idle period would otherwise be lost.
@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(doctor_router)
app.include_router(receptionist_router)
app.include_router(whatsapp_router)
