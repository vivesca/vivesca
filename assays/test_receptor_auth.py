"""Tests for metabolon.receptor_auth — centralized OAuth2 credential management."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.receptor_auth import OAuth2Config, get_credential_status, get_google_credentials


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gmail_config():
    return OAuth2Config(prefix="GMAIL", scopes=["https://mail.google.com/"])


@pytest.fixture
def gcal_config():
    return OAuth2Config(prefix="GCAL", scopes=["https://www.googleapis.com/auth/calendar"])


@pytest.fixture
def env_credentials(monkeypatch):
    """Set full env-var credentials for GMAIL."""
    monkeypatch.setenv("GMAIL_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "test-refresh-token")


@pytest.fixture
def gcal_env_credentials(monkeypatch):
    """Set full env-var credentials for GCAL."""
    monkeypatch.setenv("GCAL_CLIENT_ID", "gcal-client-id")
    monkeypatch.setenv("GCAL_CLIENT_SECRET", "gcal-client-secret")
    monkeypatch.setenv("GCAL_REFRESH_TOKEN", "gcal-refresh-token")


@pytest.fixture
def token_file(tmp_path):
    """Write a fake gog token.json."""
    token_data = {
        "client_id": "file-client-id.apps.googleusercontent.com",
        "client_secret": "file-client-secret",
        "refresh_token": "file-refresh-token",
        "type": "authorized_user",
    }
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(token_data))
    return token_path


# ---------------------------------------------------------------------------
# OAuth2Config
# ---------------------------------------------------------------------------


class TestOAuth2Config:
    def test_default_token_uri(self, gmail_config):
        assert gmail_config.token_uri == "https://oauth2.googleapis.com/token"

    def test_custom_token_uri(self):
        cfg = OAuth2Config(
            prefix="CUSTOM",
            scopes=[],
            token_uri="https://custom.example.com/token",
        )
        assert cfg.token_uri == "https://custom.example.com/token"

    def test_default_token_file_is_none(self, gmail_config):
        assert gmail_config.token_file is None

    def test_custom_token_file(self, tmp_path):
        custom = tmp_path / "my_token.json"
        cfg = OAuth2Config(prefix="X", scopes=[], token_file=custom)
        assert cfg.token_file == custom

    def test_scopes_stored(self, gmail_config):
        assert gmail_config.scopes == ["https://mail.google.com/"]


# ---------------------------------------------------------------------------
# get_google_credentials — env var path
# ---------------------------------------------------------------------------


class TestGetGoogleCredentialsFromEnv:
    def test_builds_credentials_from_env(self, gmail_config, env_credentials):
        mock_creds = MagicMock()
        mock_creds.valid = True
        with patch("metabolon.receptor_auth.Credentials") as MockCreds, patch(
            "metabolon.receptor_auth.Request"
        ):
            MockCreds.return_value = mock_creds
            result = get_google_credentials(gmail_config)
        assert result is mock_creds
        MockCreds.assert_called_once_with(
            token=None,
            refresh_token="test-refresh-token",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://mail.google.com/"],
        )

    def test_refreshes_on_creation(self, gmail_config, env_credentials):
        mock_creds = MagicMock()
        with patch("metabolon.receptor_auth.Credentials") as MockCreds, patch(
            "metabolon.receptor_auth.Request"
        ) as MockRequest:
            MockCreds.return_value = mock_creds
            get_google_credentials(gmail_config)
        mock_creds.refresh.assert_called_once_with(MockRequest.return_value)

    def test_different_prefix(self, gcal_config, gcal_env_credentials):
        mock_creds = MagicMock()
        with patch("metabolon.receptor_auth.Credentials") as MockCreds, patch(
            "metabolon.receptor_auth.Request"
        ):
            MockCreds.return_value = mock_creds
            result = get_google_credentials(gcal_config)
        assert result is mock_creds
        call_kwargs = MockCreds.call_args[1]
        assert call_kwargs["client_id"] == "gcal-client-id"
        assert call_kwargs["refresh_token"] == "gcal-refresh-token"


# ---------------------------------------------------------------------------
# get_google_credentials — token file path
# ---------------------------------------------------------------------------


class TestGetGoogleCredentialsFromTokenFile:
    def test_uses_config_token_file(self, gmail_config, token_file):
        cfg = replace(gmail_config, token_file=token_file)
        mock_creds = MagicMock()
        mock_creds.valid = True
        with patch(
            "metabolon.receptor_auth.Credentials.from_authorized_user_file"
        ) as mock_from_file:
            mock_from_file.return_value = mock_creds
            result = get_google_credentials(cfg)
        assert result is mock_creds
        mock_from_file.assert_called_once_with(
            str(token_file), ["https://mail.google.com/"]
        )

    def test_refreshes_expired_token_from_file(self, gmail_config, token_file):
        cfg = replace(gmail_config, token_file=token_file)
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "some-refresh"
        mock_creds.valid = False
        with patch(
            "metabolon.receptor_auth.Credentials.from_authorized_user_file"
        ) as mock_from_file, patch("metabolon.receptor_auth.Request"):
            mock_from_file.return_value = mock_creds
            result = get_google_credentials(cfg)
        assert result is mock_creds
        mock_creds.refresh.assert_called_once()

    def test_returns_valid_cached_creds(self, gmail_config, token_file):
        cfg = replace(gmail_config, token_file=token_file)
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds.valid = True
        with patch(
            "metabolon.receptor_auth.Credentials.from_authorized_user_file"
        ) as mock_from_file:
            mock_from_file.return_value = mock_creds
            result = get_google_credentials(cfg)
        assert result is mock_creds
        mock_creds.refresh.assert_not_called()

    def test_nonexistent_token_file_falls_through(self, gmail_config, tmp_path):
        cfg = replace(gmail_config, token_file=tmp_path / "nonexistent.json")
        # No env vars, no file — should raise
        with pytest.raises(RuntimeError, match="auth failed"):
            get_google_credentials(cfg)


# ---------------------------------------------------------------------------
# get_google_credentials — priority: env vars before token file
# ---------------------------------------------------------------------------


class TestCredentialPriority:
    def test_env_takes_priority_over_file(
        self, gmail_config, env_credentials, token_file
    ):
        cfg = replace(gmail_config, token_file=token_file)
        mock_creds = MagicMock()
        with patch("metabolon.receptor_auth.Credentials") as MockCreds, patch(
            "metabolon.receptor_auth.Request"
        ):
            MockCreds.return_value = mock_creds
            get_google_credentials(cfg)
        # Should use env path (Credentials constructor), not file path
        MockCreds.assert_called_once()


# ---------------------------------------------------------------------------
# get_google_credentials — missing credentials
# ---------------------------------------------------------------------------


class TestMissingCredentials:
    def test_raises_when_no_env_and_no_file(self, gmail_config, monkeypatch):
        # Clear any env vars
        for suffix in ("CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN"):
            monkeypatch.delenv(f"GMAIL_{suffix}", raising=False)
        # No token_file set, no default
        with pytest.raises(RuntimeError, match="auth failed"):
            get_google_credentials(gmail_config)

    def test_partial_env_raises(self, gmail_config, monkeypatch):
        monkeypatch.setenv("GMAIL_CLIENT_ID", "only-id")
        # No CLIENT_SECRET or REFRESH_TOKEN
        monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GMAIL_REFRESH_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="auth failed"):
            get_google_credentials(gmail_config)


# ---------------------------------------------------------------------------
# get_credential_status
# ---------------------------------------------------------------------------


class TestGetCredentialStatus:
    def test_available_env(self, gmail_config, env_credentials):
        with patch("metabolon.receptor_auth.get_google_credentials") as mock_get:
            mock_get.return_value = MagicMock(valid=True)
            status = get_credential_status(gmail_config)
        assert status["available"] is True
        assert status["source"] == "env_vars"
        assert status["prefix"] == "GMAIL"

    def test_available_file(self, gmail_config, token_file):
        cfg = replace(gmail_config, token_file=token_file)
        with patch("metabolon.receptor_auth.get_google_credentials") as mock_get:
            mock_get.return_value = MagicMock(valid=True)
            status = get_credential_status(cfg)
        assert status["available"] is True
        assert status["source"] == "token_file"

    def test_unavailable(self, gmail_config, monkeypatch):
        for suffix in ("CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN"):
            monkeypatch.delenv(f"GMAIL_{suffix}", raising=False)
        status = get_credential_status(gmail_config)
        assert status["available"] is False
        assert status["source"] is None
        assert "error" in status

    def test_has_scopes_in_status(self, gmail_config, env_credentials):
        with patch("metabolon.receptor_auth.get_google_credentials") as mock_get:
            mock_get.return_value = MagicMock(valid=True)
            status = get_credential_status(gmail_config)
        assert status["scopes"] == ["https://mail.google.com/"]
