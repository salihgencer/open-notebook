import re
from typing import ClassVar, Literal, Optional

from open_notebook.domain.base import ObjectModel

VALID_ROLES = ("admin", "editor", "viewer")
Role = Literal["admin", "editor", "viewer"]


class User(ObjectModel):
    table_name: ClassVar[str] = "ext_user"
    email: str
    name: str
    password_hash: Optional[str] = None
    role: Role = "editor"
    locale: str = "en"
    is_active: bool = True

    @classmethod
    def _validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @classmethod
    def _validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Invalid role: {v}. Must be one of {VALID_ROLES}")
        return v

    def __init__(self, **data):
        if "email" in data:
            data["email"] = self._validate_email(data["email"])
        if "role" in data:
            data["role"] = self._validate_role(data["role"])
        super().__init__(**data)


class Session(ObjectModel):
    table_name: ClassVar[str] = "ext_session"
    user_id: str
    refresh_token: str
    expires_at: str
    is_revoked: bool = False


class NotebookShare(ObjectModel):
    table_name: ClassVar[str] = "ext_notebook_share"
    notebook_id: str
    user_id: str
    permission: Literal["editor", "viewer"] = "viewer"
