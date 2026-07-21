# app/core/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings

# Create the Limiter instance. It will use the client's IP address as the default key.
limiter = Limiter(key_func=get_remote_address)

# We'll define some default limits that can be overridden per route.
default_limits = ["100/minute"]

# a custom key function that uses the authenticated user ID if available,
# falling back to IP for anonymous requests.
async def user_or_ip_key(request: Request) -> str:
    # Try to get user from the request state (we'll set this in a dependency)
    if hasattr(request.state, "user_id") and request.state.user_id is not None:
        return f"user:{request.state.user_id}"
    return get_remote_address(request)

# If we want per-user limits, we can create a second limiter using this key.
user_limiter = Limiter(key_func=user_or_ip_key)