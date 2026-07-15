from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import router as v1_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)
app.include_router(v1_router)

@app.get("/", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}