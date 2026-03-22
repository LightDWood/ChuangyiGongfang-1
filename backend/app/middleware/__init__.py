from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status


class JWTAuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = [
        "/",
        "/api/health",
        "/api/auth/login",
        "/api/auth/register",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        if request.url.path.endswith("/stream"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"},
            )

        token = auth_header.split(" ")[1]
        from .services.auth_service import decode_token

        user_id = decode_token(token)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )

        request.state.user_id = user_id
        return await call_next(request)
