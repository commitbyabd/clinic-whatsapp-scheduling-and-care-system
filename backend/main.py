from logging_config import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.doctor import router as doctor_router
from app.routers.whatsapp import router as whatsapp_router
from chatbot.settings import classifier_settings, openai_settings, twilio_settings
from logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()

    # Say out loud which optional pieces are actually live. Without this you
    # discover a missing key when a patient message silently takes the wrong
    # path, rather than in the first ten lines of the server log.
    for setting in (twilio_settings, openai_settings, classifier_settings):
        logger.info(setting.explain())

    yield  # app runs here, serving requests
    await close_mongo_connection()  # runs once, at shutdown


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
app.include_router(whatsapp_router)
