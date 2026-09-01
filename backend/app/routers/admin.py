from fastapi import APIRouter

from app.features.admin.route import router as admin_feature_router

router = APIRouter()
router.include_router(admin_feature_router)
