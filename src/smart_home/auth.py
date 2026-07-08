from __future__ import annotations

import hashlib
import os
import secrets
from typing import Any

from .database import Database


PASSWORD_SALT = os.getenv("SMART_HOME_PASSWORD_SALT", "se-final-smart-home-2026")


def hash_password(password: str) -> str:
    return hashlib.sha256(f"{PASSWORD_SALT}:{password}".encode("utf-8")).hexdigest()


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self._tokens: dict[str, dict[str, Any]] = {}

    def login(self, username: str, password: str) -> dict[str, Any]:
        user = self.db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        if not user or user["password_hash"] != hash_password(password):
            raise AuthError("用户名或密码错误。")
        token = secrets.token_urlsafe(24)
        safe_user = self._safe_user(user)
        self._tokens[token] = safe_user
        return {"token": token, "user": safe_user}

    def get_user(self, token: str | None) -> dict[str, Any]:
        if not token or token not in self._tokens:
            raise AuthError("请先登录。")
        return self._tokens[token]

    def require(self, user: dict[str, Any], allowed_roles: set[str]) -> None:
        if user["role"] not in allowed_roles:
            raise PermissionError("当前角色没有执行该操作的权限。")

    @staticmethod
    def _safe_user(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "display_name": row["display_name"],
        }
