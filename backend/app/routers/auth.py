from fastapi import APIRouter

from app.features.auth.route import router as auth_feature_router

router = APIRouter()
router.include_router(auth_feature_router)
