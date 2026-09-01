from fastapi import APIRouter

from app.features.doctor.route import router as doctor_feature_router

router = APIRouter()
router.include_router(doctor_feature_router)
