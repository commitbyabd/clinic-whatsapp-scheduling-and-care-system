from fastapi import APIRouter

from app.features.receptionist.route import router as receptionist_feature_router

router = APIRouter()
router.include_router(receptionist_feature_router)
