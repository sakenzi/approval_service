import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.router import api_route, health_route
from core.config import settings

logging.basicConfig(level=getattr(settings, "LOG_LEVEL", "INFO"))
logger = logging.getLogger("approval_service")

app = FastAPI(
    title="approval-service",
    description="Сервис согласования контента перед публикацией.",
    version="1.0.0",
)

app.include_router(health_route)
app.include_router(api_route, prefix="/api")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})