from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.approval_requests.approval_api import router as approval_router

health_route = health_router
api_route = APIRouter()
api_route.include_router(approval_router, tags=["approval-requests"])
