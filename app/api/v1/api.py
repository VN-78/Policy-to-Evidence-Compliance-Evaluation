from fastapi import APIRouter
from app.api.v1.compliance import router as compliance_router
from app.api.v1.policies import router as policies_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(policies_router)
api_router.include_router(compliance_router)