"""
SmartRescue AI — Rate Limiter
SlowAPI integration for per-route API rate limiting.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For for proxied requests."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["60/minute"],
    storage_uri="memory://",
)


def setup_rate_limiting(app):
    """Attach rate limiter to FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
