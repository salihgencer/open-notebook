from typing import List, Optional

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from extensions.auth.service import AuthService


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_service: AuthService,
        excluded_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
            )

        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
            )

        try:
            payload = self.auth_service.decode_token(token)
            if payload.get("type") != "access":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token type"},
                )
            request.state.user = payload
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
            )

        return await call_next(request)
