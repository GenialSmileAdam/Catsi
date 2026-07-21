from fastapi import FastAPI, Depends
from app.core.config import settings
from app.api.v1.router import router as v1_router
from app.db.database import engine, Base
from contextlib import asynccontextmanager
from app.schemas.user import UserResponse
from app.api.v1.dependencies import get_current_user
from app.core.rate_limiter import limiter
from fastapi.responses import JSONResponse
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from app.models.user import User
import app.models
import asyncio
from dotenv import load_dotenv


load_dotenv()


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

# Attach the limiter to the app state (needed for the middleware)
app.state.limiter = limiter

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": str(exc.retry_after) if exc.retry_after else "60"},
    )


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