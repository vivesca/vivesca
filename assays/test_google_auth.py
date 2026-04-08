"""Tests for metabolon.organelles.google_auth — shared Google OAuth2 credentials."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.google_auth import (
    CALENDAR_SCOPES,
    DEFAULT_TOKEN_FILE,
    GMAIL_SCOPES,
    build_service,
    get_credentials,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_creds(*, valid=True, expired=False, refresh_token="rt123", token="tok"):
    """Create a mock Credentials object."""
    creds = MagicMock()
    creds.valid = valid
    creds.expired = expired
    creds.refresh_token = refresh_token
    creds.token = token
    creds.scopes = ["https://www.googleapis.com/auth/test"]
    return creds


# ---------------------------------------------------------------------------
# get_credentials — env var path
# ---------------------------------------------------------------------------


class TestGetCredentialsFromEnvVars:
    """When all three env vars are set, build creds and refresh them."""

    def test_builds_creds_from_env_vars(self):
        env = {
            "GOOGLE_CLIENT_ID": "cid",
            "GOOGLE_CLIENT_SECRET": "csec",
            "GOOGLE_REFRESH_TOKEN": "rtok",
        }
        mock_creds = _make_creds()
        with (
            patch.dict(os.environ, env, clear=False),
            patch("metabolon.organelles.google_auth.Credentials", return_value=mock_creds),
            patch("metabolon.organelles.google_auth.Request"),
        ):
            result = get_credentials(scopes=["https://www.googleapis.com/auth/test"])
            assert result is mock_creds
            # Credentials constructor called with env var values
            _, kwargs = mock_creds.call_args if mock_creds.call_args else ((), {})
            # The constructor was called (Credentials is mocked)
            assert mock_creds.refresh.called

    def test_refreshes_creds_after_building(self):
        env = {
            "GOOGLE_CLIENT_ID": "cid",
            "GOOGLE_CLIENT_SECRET": "csec",
            "GOOGLE_REFRESH_TOKEN": "rtok",
        }
        mock_creds = _make_creds()
        with (
            patch.dict(os.environ, env, clear=False),
            patch("metabolon.organelles.google_auth.Credentials", return_value=mock_creds),
            patch("metabolon.organelles.google_auth.Request") as MockReq,
        ):
            get_credentials(scopes=["https://www.googleapis.com/auth/test"])
            mock_creds.refresh.assert_called_once_with(MockReq.return_value)


# ---------------------------------------------------------------------------
# get_credentials — token file path
# ---------------------------------------------------------------------------


class TestGetCredentialsFromTokenFile:
    """When env vars are missing, fall back to gog token.json."""

    def test_reads_token_file(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_data = {
            "client_id": "file_cid",
            "client_secret": "file_csec",
            "refresh_token": "file_rt",
            "type": "authorized_user",
        }
        token_file.write_text(json.dumps(token_data))

        mock_creds = _make_creds()
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("metabolon.organelles.google_auth.Credentials") as MockCreds,
            patch("metabolon.organelles.google_auth.Request"),
        ):
            MockCreds.from_authorized_user_file.return_value = mock_creds
            result = get_credentials(
                scopes=["https://www.googleapis.com/auth/test"],
                token_file=token_file,
            )
            assert result is mock_creds
            MockCreds.from_authorized_user_file.assert_called_once()

    def test_refreshes_expired_token_file_creds(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text("{}")

        mock_creds = _make_creds(valid=False, expired=True)
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("metabolon.organelles.google_auth.Credentials") as MockCreds,
            patch("metabolon.organelles.google_auth.Request") as MockReq,
        ):
            MockCreds.from_authorized_user_file.return_value = mock_creds
            get_credentials(
                scopes=["https://www.googleapis.com/auth/test"],
                token_file=token_file,
            )
            mock_creds.refresh.assert_called_once_with(MockReq.return_value)

    def test_returns_valid_creds_without_refresh(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text("{}")

        mock_creds = _make_creds(valid=True, expired=False)
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("metabolon.organelles.google_auth.Credentials") as MockCreds,
            patch("metabolon.organelles.google_auth.Request"),
        ):
            MockCreds.from_authorized_user_file.return_value = mock_creds
            result = get_credentials(
                scopes=["https://www.googleapis.com/auth/test"],
                token_file=token_file,
            )
            assert result is mock_creds
            # Should NOT refresh — already valid
            mock_creds.refresh.assert_not_called()


# ---------------------------------------------------------------------------
# get_credentials — errors
# ---------------------------------------------------------------------------


class TestGetCredentialsErrors:
    """Raise clear errors when no credentials are available."""

    def test_raises_when_no_env_vars_and_no_token_file(self, tmp_path):
        with (
            patch.dict(os.environ, {}, clear=False),
            pytest.raises(RuntimeError, match="Google auth failed"),
        ):
            get_credentials(
                scopes=["https://www.googleapis.com/auth/test"],
                token_file=tmp_path / "nonexistent.json",
            )

    def test_raises_when_token_file_has_invalid_creds(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text("{}")

        with (
            patch.dict(os.environ, {}, clear=False),
            patch("metabolon.organelles.google_auth.Credentials") as MockCreds,
            pytest.raises(RuntimeError, match="Google auth failed"),
        ):
            # from_authorized_user_file returns None
            MockCreds.from_authorized_user_file.return_value = None
            get_credentials(
                scopes=["https://www.googleapis.com/auth/test"],
                token_file=token_file,
            )


# ---------------------------------------------------------------------------
# get_credentials — env var prefix
# ---------------------------------------------------------------------------


class TestEnvVarPrefix:
    """Support custom env var prefixes for different services."""

    def test_uses_custom_prefix(self):
        env = {
            "GMAIL_CLIENT_ID": "gm_cid",
            "GMAIL_CLIENT_SECRET": "gm_csec",
            "GMAIL_REFRESH_TOKEN": "gm_rt",
        }
        mock_creds = _make_creds()
        with (
            patch.dict(os.environ, env, clear=False),
            patch("metabolon.organelles.google_auth.Credentials", return_value=mock_creds),
            patch("metabolon.organelles.google_auth.Request"),
        ):
            get_credentials(
                scopes=["https://www.googleapis.com/auth/gmail"],
                env_prefix="GMAIL",
            )
            # The mock Credentials was constructed with GMAIL_ prefixed values
            # Since Credentials is mocked, we verify it was called at all
            assert mock_creds.refresh.called


# ---------------------------------------------------------------------------
# get_credentials — service-specific scopes
# ---------------------------------------------------------------------------


class TestScopePropagation:
    """Scopes are passed through to the Credentials constructor."""

    def test_scopes_passed_to_credentials(self):
        env = {
            "GOOGLE_CLIENT_ID": "cid",
            "GOOGLE_CLIENT_SECRET": "csec",
            "GOOGLE_REFRESH_TOKEN": "rtok",
        }
        mock_creds = _make_creds()
        with (
            patch.dict(os.environ, env, clear=False),
            patch("metabolon.organelles.google_auth.Credentials", return_value=mock_creds) as MockCreds,
            patch("metabolon.organelles.google_auth.Request"),
        ):
            scopes = [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
            ]
            get_credentials(scopes=scopes)
            call_kwargs = MockCreds.call_args[1]
            assert call_kwargs["scopes"] == scopes


# ---------------------------------------------------------------------------
# build_service — convenience wrapper
# ---------------------------------------------------------------------------


class TestBuildService:
    """build_service() returns an authenticated Google API service object."""

    def test_builds_service_with_credentials(self):
        mock_creds = _make_creds()
        mock_service = MagicMock()
        with (
            patch(
                "metabolon.organelles.google_auth.get_credentials", return_value=mock_creds
            ),
            patch("metabolon.organelles.google_auth.build", return_value=mock_service) as mock_build,
        ):
            result = build_service(
                api="calendar",
                version="v3",
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            assert result is mock_service
            mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Module exposes useful defaults."""

    def test_default_token_file_path(self):
        expected = Path.home() / ".config" / "gog" / "token.json"
        assert DEFAULT_TOKEN_FILE == expected

    def test_well_known_scopes(self):
        assert "https://www.googleapis.com/auth/calendar" in CALENDAR_SCOPES
        assert "https://www.googleapis.com/auth/gmail.modify" in GMAIL_SCOPES
