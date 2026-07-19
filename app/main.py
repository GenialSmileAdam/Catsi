from fastapi import FastAPI, Depends
from app.core.config import settings
from app.api.v1.router import router as v1_router
from app.db.database import engine, Base
from contextlib import asynccontextmanager
from app.schemas.user import UserResponse
from app.api.v1.dependencies import get_current_user
from app.models.user import User
import app.models
import asyncio


# This lifespan runs startup/shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.services.vector_store import get_or_create_collection

    await asyncio.to_thread(get_or_create_collection)

    yield
    # Shutdown: dispose engine
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)
app.include_router(v1_router)

@app.get("/", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/users/me", response_model=UserResponse, tags=["protected"])
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/debug/env")
async def debug_env():
    import os
    return {
        "LANGCHAIN_TRACING": os.environ.get("LANGCHAIN_TRACING"),
        "LANGCHAIN_TRACING_V2": os.environ.get("LANGCHAIN_TRACING_V2"),
        "LANGCHAIN_HANDLER": os.environ.get("LANGCHAIN_HANDLER"),
        "LANGCHAIN_PROJECT": os.environ.get("LANGCHAIN_PROJECT"),
        "LANGCHAIN_ENDPOINT": os.environ.get("LANGCHAIN_ENDPOINT"),
        "LANGCHAIN_API_KEY": os.environ.get("LANGCHAIN_API_KEY", "***")[:8] + "...",
    }