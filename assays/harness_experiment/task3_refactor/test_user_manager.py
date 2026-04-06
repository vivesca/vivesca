"""Tests for UserManager."""

import pytest
from user_manager import UserManager


@pytest.fixture
def manager():
    return UserManager()


def test_create_user(manager):
    user = manager.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"


def test_create_duplicate_raises(manager):
    manager.create_user("alice", "a@b.com")
    with pytest.raises(ValueError):
        manager.create_user("alice", "a@b.com")


def test_get_user(manager):
    manager.create_user("bob", "bob@b.com")
    assert manager.get_user("bob")["email"] == "bob@b.com"


def test_get_missing_returns_none(manager):
    assert manager.get_user("nobody") is None


def test_delete_user(manager):
    manager.create_user("charlie", "c@c.com")
    assert manager.delete_user("charlie")
    assert manager.get_user("charlie") is None


def test_list_users(manager):
    manager.create_user("a", "a@a.com")
    manager.create_user("b", "b@b.com")
    assert sorted(manager.list_users()) == ["a", "b"]
