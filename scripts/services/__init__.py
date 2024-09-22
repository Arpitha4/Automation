from fastapi import APIRouter

from scripts.services import parameter_services

router = APIRouter()
router.include_router(parameter_services.ut_app_router)
