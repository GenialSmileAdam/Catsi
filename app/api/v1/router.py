from fastapi import APIRouter

# This is the main v1 router. Later we'll include other routers here.
router = APIRouter(prefix="/api/v1")


@router.get("/ping", tags=["health"])
async def ping():
    """Ping endpoint inside v1 API."""
    return {"ping": "pong!"}