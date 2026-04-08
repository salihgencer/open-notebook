import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from loguru import logger


class AuthService:
    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ):
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "")
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET must be set")
        self.access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(access_token_expire_minutes))
        )
        self.refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", str(refresh_token_expire_days))
        )

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        locale: str,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "locale": locale,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def create_refresh_token(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
