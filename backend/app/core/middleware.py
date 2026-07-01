"""Optional API key middleware for single-user VPS deployments."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

# Paths that never require an API key
PUBLIC_PATHS = {"/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header when API_KEY is set in environment."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()

        if not settings.api_key:
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key")
        if provided != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key", "success": False},
            )

        return await call_next(request)
