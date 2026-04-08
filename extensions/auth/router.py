from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import repo_create, repo_query
from extensions.auth.service import AuthService


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    locale: Optional[str] = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    email: str
    name: str
    role: str
    locale: str


def create_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter()

    @router.post("/register", status_code=201)
    async def register(req: RegisterRequest):
        existing = await repo_query(
            "SELECT id FROM ext_user WHERE email = $email",
            {"email": req.email.lower()},
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        password_hash = auth_service.hash_password(req.password)
        result = await repo_create(
            "ext_user",
            {
                "email": req.email.lower(),
                "name": req.name,
                "password_hash": password_hash,
                "role": "editor",
                "locale": req.locale or "en",
                "is_active": True,
            },
        )
        user_data = result[0] if isinstance(result, list) else result
        user_id = user_data["id"]

        access_token = auth_service.create_access_token(
            user_id=user_id,
            email=user_data["email"],
            role=user_data["role"],
            locale=user_data["locale"],
        )
        refresh_token = auth_service.create_refresh_token(user_id=user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            locale=user_data["locale"],
        )

    @router.post("/login")
    async def login(req: LoginRequest):
        users = await repo_query(
            "SELECT * FROM ext_user WHERE email = $email",
            {"email": req.email.lower()},
        )
        if not users:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = users[0]
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account disabled")

        if not auth_service.verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = auth_service.create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )
        refresh_token = auth_service.create_refresh_token(user_id=user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            email=user["email"],
            name=user["name"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )

    @router.post("/refresh")
    async def refresh(req: RefreshRequest):
        try:
            payload = auth_service.decode_token(req.refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

        user_id = payload["sub"]
        users = await repo_query(
            "SELECT * FROM $id",
            {"id": user_id},
        )
        if not users:
            raise HTTPException(status_code=401, detail="User not found")

        user = users[0]
        access_token = auth_service.create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )
        new_refresh = auth_service.create_refresh_token(user_id=user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            email=user["email"],
            name=user["name"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )

    @router.get("/me")
    async def me(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {
            "id": user["sub"],
            "email": user["email"],
            "role": user["role"],
            "locale": user["locale"],
        }

    return router
