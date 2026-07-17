from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.document import router as documents_router

# This is the main v1 router. Later we'll include other routers here.
router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(documents_router)

@router.get("/ping", tags=["health"])
async def ping():
    """Ping endpoint inside v1 API."""
    return {"ping": "pong!"}