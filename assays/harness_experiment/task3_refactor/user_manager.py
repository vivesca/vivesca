"""UserManager — handles user CRUD operations."""

from __future__ import annotations


class UserManager:
    """Manages user accounts."""

    def __init__(self):
        self._users: dict[str, dict] = {}

    def create_user(self, username: str, email: str) -> dict:
        if username in self._users:
            raise ValueError(f"User {username} already exists")
        user = {"username": username, "email": email, "active": True}
        self._users[username] = user
        return user

    def get_user(self, username: str) -> dict | None:
        return self._users.get(username)

    def delete_user(self, username: str) -> bool:
        if username in self._users:
            del self._users[username]
            return True
        return False

    def list_users(self) -> list[str]:
        return list(self._users.keys())
