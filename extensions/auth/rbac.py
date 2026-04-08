from typing import Any, Callable, Dict

from fastapi import HTTPException, Request

ROLE_HIERARCHY = {
    "admin": 3,
    "editor": 2,
    "viewer": 1,
}


def get_current_user_from_state(request: Request) -> Dict[str, Any]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_role(minimum_role: str) -> Callable:
    minimum_level = ROLE_HIERARCHY.get(minimum_role, 0)

    def checker(request: Request) -> Dict[str, Any]:
        user = get_current_user_from_state(request)
        user_level = ROLE_HIERARCHY.get(user.get("role", ""), 0)
        if user_level < minimum_level:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.get('role')}' insufficient. Requires '{minimum_role}' or higher.",
            )
        return user

    return checker
