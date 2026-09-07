from fastapi import APIRouter

from app.features.whatsapp.route import router as whatsapp_feature_router

router = APIRouter()
router.include_router(whatsapp_feature_router)
