from datetime import datetime
from typing import Optional, Any

from pydantic import field_validator, Field, BaseModel
from fastapi import Request
from rfc9457 import UnauthorisedProblem, BadRequestProblem


class User(BaseModel):
    id: str = Field(..., description="Уникальный ID пользователя")
    email: str = Field("", description="Email пользователя")
    role: list[str] = Field(default_factory=list, description="Роли пользователя")
    permissions: list[str] = Field(default_factory=list, description="Список разрешений")
    token_expires: Optional[datetime] = Field(None, description="Время истечения токена")

    model_config = {
        "validate_assignment": True,
    }


    @classmethod
    def parse_lists(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(',') if p.strip()]
        return v or []

    @field_validator('permissions', mode='before')
    @classmethod
    def parse_permissions(cls, v: Any) -> list[str]:
        return cls.parse_lists(v)

    @field_validator('role', mode='before')
    @classmethod
    def parse_role(cls, v: Any) -> list[str]:
        return cls.parse_lists(v)

    @field_validator('token_expires', mode='before')
    @classmethod
    def parse_expires(cls, v: Any) -> Optional[datetime]:
        if isinstance(v, str) and v.isdigit():
            try:
                return datetime.fromtimestamp(int(v))
            except (ValueError, OSError):
                return None
        return v

    @property
    def is_admin(self) -> bool:
        return "admin" in [r.lower() for r in self.role]

    @property
    def is_token_expired(self) -> bool:
        if not self.token_expires:
            return False
        return datetime.now() > self.token_expires

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_any_permission(self, *permissions: str) -> bool:
        return any(perm in self.permissions for perm in permissions)

    def has_all_permissions(self, *permissions: str) -> bool:
        return all(perm in self.permissions for perm in permissions)

    def has_role(self, role: str) -> bool:
        return role.lower() in [r.lower() for r in self.role]

    def has_any_role(self, *roles: str) -> bool:
        user_roles = [r.lower() for r in self.role]
        return any(role.lower() in user_roles for role in roles)

    def has_all_roles(self, *roles: str) -> bool:
        user_roles = [r.lower() for r in self.role]
        return all(role.lower() in user_roles for role in roles)


def get_user(request: Request) -> User:
    user_id = request.headers.get("X-User-ID")
    user_email = request.headers.get("X-User-Email", "")
    user_role = request.headers.get("X-User-Role", "")
    token_expires = request.headers.get("X-Token-Expires")
    permissions = request.headers.get("X-Permissions", "")

    if not user_id:
        raise UnauthorisedProblem(
            detail="Missing X-User-ID header"
        )

    try:
        user = User(
            id=user_id,
            email=user_email,
            role=user_role,
            permissions=permissions,
            token_expires=token_expires
        )
        return user
    except ValueError as e:
        raise BadRequestProblem(
            detail=f"Invalid user data in headers: {str(e)}"
        )
