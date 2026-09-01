from logging_config import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.doctor import router as doctor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
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


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(doctor_router)
