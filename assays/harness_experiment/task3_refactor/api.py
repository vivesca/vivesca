"""API layer — delegates to UserManager."""

from user_manager import UserManager


def create_app() -> dict:
    """Create application with UserManager dependency."""
    manager = UserManager()
    return {"manager": manager, "version": "1.0"}


def handle_create(app: dict, username: str, email: str) -> dict:
    """Handle user creation request."""
    manager: UserManager = app["manager"]
    return manager.create_user(username, email)


def handle_list(app: dict) -> list[str]:
    """List all users via UserManager."""
    manager: UserManager = app["manager"]
    return manager.list_users()
