"""Tests for metabolon.organelles.oauth2 — centralized OAuth2 authentication."""

import time
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# TokenStore
# ---------------------------------------------------------------------------


class TestTokenStore:
    """Token persistence layer."""

    def test_save_and_load_roundtrip(self, tmp_path):
        from metabolon.organelles.oauth2 import TokenStore

        store = TokenStore(tmp_path / "tokens")
        token = {
            "access_token": "ya29.a0",
            "refresh_token": "1//0abc",
            "expires_at": time.time() + 3600,
            "scope": "https://www.googleapis.com/auth/gmail.modify",
        }
        store.save("gmail", token)
        loaded = store.load("gmail")
        assert loaded is not None
        assert loaded["access_token"] == "ya29.a0"
        assert loaded["refresh_token"] == "1//0abc"

    def test_load_missing_returns_none(self, tmp_path):
        from metabolon.organelles.oauth2 import TokenStore

        store = TokenStore(tmp_path / "tokens")
        assert store.load("nonexistent") is None

    def test_save_creates_directory(self, tmp_path):
        from metabolon.organelles.oauth2 import TokenStore

        deep = tmp_path / "a" / "b" / "c"
        store = TokenStore(deep)
        store.save("svc", {"access_token": "x"})
        assert (deep / "svc.json").exists()

    def test_delete_removes_token(self, tmp_path):
        from metabolon.organelles.oauth2 import TokenStore

        store = TokenStore(tmp_path / "tokens")
        store.save("svc", {"access_token": "x"})
        assert store.load("svc") is not None
        store.delete("svc")
        assert store.load("svc") is None

    def test_delete_nonexistent_is_noop(self, tmp_path):
        from metabolon.organelles.oauth2 import TokenStore

        store = TokenStore(tmp_path / "tokens")
        store.delete("ghost")  # should not raise


# ---------------------------------------------------------------------------
# OAuth2Config
# ---------------------------------------------------------------------------


class TestOAuth2Config:
    """Configuration dataclass."""

    def test_from_env(self):
        from metabolon.organelles.oauth2 import OAuth2Config

        env = {
            "GMAIL_CLIENT_ID": "cid",
            "GMAIL_CLIENT_SECRET": "csec",
            "GMAIL_TOKEN_URI": "https://oauth2.googleapis.com/token",
            "GMAIL_AUTH_URI": "https://accounts.google.com/o/oauth2/v2/auth",
            "GMAIL_SCOPES": "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.readonly",
        }
        cfg = OAuth2Config.from_env("gmail", env)
        assert cfg.client_id == "cid"
        assert cfg.client_secret == "csec"
        assert len(cfg.scopes) == 2

    def test_from_env_uses_defaults(self):
        from metabolon.organelles.oauth2 import OAuth2Config

        env = {
            "MYAPI_CLIENT_ID": "cid",
            "MYAPI_CLIENT_SECRET": "csec",
        }
        cfg = OAuth2Config.from_env("myapi", env)
        assert cfg.token_uri == "https://oauth2.googleapis.com/token"
        assert cfg.auth_uri == "https://accounts.google.com/o/oauth2/v2/auth"

    def test_from_env_missing_client_id_raises(self):
        from metabolon.organelles.oauth2 import OAuth2Config

        with pytest.raises(ValueError, match="CLIENT_ID"):
            OAuth2Config.from_env("svc", {})


# ---------------------------------------------------------------------------
# OAuth2Client
# ---------------------------------------------------------------------------


class TestOAuth2Client:
    """High-level OAuth2 operations."""

    def _make_client(self, tmp_path):
        from metabolon.organelles.oauth2 import OAuth2Client, OAuth2Config

        cfg = OAuth2Config(
            client_id="cid",
            client_secret="csec",
            token_uri="https://example.com/token",
            auth_uri="https://example.com/auth",
            scopes=["read", "write"],
            redirect_uri="http://localhost:8080/callback",
        )
        store_dir = tmp_path / "tokens"
        return OAuth2Client(cfg, store_dir=store_dir)

    def test_authorization_url(self, tmp_path):
        client = self._make_client(tmp_path)
        url, state, verifier = client.authorization_url()
        assert "client_id=cid" in url
        assert "scope=read+write" in url
        assert "code_challenge=" in url
        assert state
        assert verifier

    def test_exchange_code(self, tmp_path):
        client = self._make_client(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "at_new",
            "refresh_token": "rt_new",
            "expires_in": 3600,
            "scope": "read write",
        }

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            token = client.exchange_code("auth_code_123", code_verifier="verifier_abc")

        assert token["access_token"] == "at_new"
        assert token["refresh_token"] == "rt_new"
        assert "expires_at" in token
        mock_post.assert_called_once()
        call_body = mock_post.call_args
        assert (
            call_body.kwargs.get("data", {}).get("code") == "auth_code_123"
            or call_body[1].get("data", {}).get("code") == "auth_code_123"
        )

    def test_exchange_code_saves_token(self, tmp_path):
        client = self._make_client(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "at_new",
            "refresh_token": "rt_new",
            "expires_in": 3600,
        }

        with patch("httpx.post", return_value=mock_resp):
            client.exchange_code("code", code_verifier="v")

        assert client.store.load("default") is not None

    def test_refresh_token(self, tmp_path):
        client = self._make_client(tmp_path)
        # Seed a token
        client.store.save(
            "default",
            {
                "access_token": "old_at",
                "refresh_token": "rt_abc",
                "expires_at": time.time() - 100,
            },
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "new_at",
            "expires_in": 3600,
        }

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            token = client.refresh()

        assert token["access_token"] == "new_at"
        assert token["refresh_token"] == "rt_abc"  # preserved
        mock_post.assert_called_once()

    def test_refresh_no_saved_token_raises(self, tmp_path):
        client = self._make_client(tmp_path)
        with pytest.raises(RuntimeError, match="No saved token"):
            client.refresh()

    def test_get_valid_token_still_valid(self, tmp_path):
        client = self._make_client(tmp_path)
        client.store.save(
            "default",
            {
                "access_token": "at_good",
                "refresh_token": "rt",
                "expires_at": time.time() + 3600,
            },
        )

        token = client.get_valid_token()
        assert token["access_token"] == "at_good"

    def test_get_valid_token_auto_refreshes(self, tmp_path):
        client = self._make_client(tmp_path)
        client.store.save(
            "default",
            {
                "access_token": "expired",
                "refresh_token": "rt",
                "expires_at": time.time() - 100,
            },
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "refreshed",
            "expires_in": 3600,
        }

        with patch("httpx.post", return_value=mock_resp):
            token = client.get_valid_token()

        assert token["access_token"] == "refreshed"

    def test_exchange_code_http_error_raises(self, tmp_path):
        client = self._make_client(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "invalid_grant"

        with patch("httpx.post", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="Token exchange failed"):
                client.exchange_code("bad_code", code_verifier="v")

    def test_service_name_isolation(self, tmp_path):
        """Tokens for different service names don't collide."""
        from metabolon.organelles.oauth2 import OAuth2Client, OAuth2Config

        cfg = OAuth2Config(
            client_id="cid",
            client_secret="csec",
            token_uri="https://example.com/token",
            auth_uri="https://example.com/auth",
            scopes=["read"],
        )
        client_a = OAuth2Client(cfg, store_dir=tmp_path / "tokens", service="gmail")
        client_b = OAuth2Client(cfg, store_dir=tmp_path / "tokens", service="calendar")

        client_a.store.save("gmail", {"access_token": "a_token"})
        client_b.store.save("calendar", {"access_token": "b_token"})

        assert client_a.store.load("gmail")["access_token"] == "a_token"
        assert client_b.store.load("calendar")["access_token"] == "b_token"

    def test_revoke_token(self, tmp_path):
        client = self._make_client(tmp_path)
        client.store.save(
            "default",
            {
                "access_token": "at_revoke",
                "refresh_token": "rt_revoke",
                "expires_at": time.time() + 3600,
            },
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            client.revoke()

        assert client.store.load("default") is None
        mock_post.assert_called_once()

    def test_get_auth_header(self, tmp_path):
        client = self._make_client(tmp_path)
        client.store.save(
            "default",
            {
                "access_token": "bearer_tok",
                "refresh_token": "rt",
                "expires_at": time.time() + 3600,
            },
        )
        header = client.get_auth_header()
        assert header == {"Authorization": "Bearer bearer_tok"}


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


class TestForService:
    """Quick construction from env vars."""

    def test_for_service_google(self):
        from metabolon.organelles.oauth2 import for_service

        env = {
            "GOOGLE_CLIENT_ID": "gcid",
            "GOOGLE_CLIENT_SECRET": "gcsec",
            "GOOGLE_SCOPES": "https://www.googleapis.com/auth/gmail.modify",
        }
        client = for_service("google", env=env)
        assert client.cfg.client_id == "gcid"
        assert client.cfg.scopes == ["https://www.googleapis.com/auth/gmail.modify"]

    def test_for_service_custom_prefix(self):
        from metabolon.organelles.oauth2 import for_service

        env = {
            "SLACK_CLIENT_ID": "sid",
            "SLACK_CLIENT_SECRET": "ssec",
            "SLACK_SCOPES": "channels:read chat:write",
            "SLACK_TOKEN_URI": "https://slack.com/api/oauth.token",
            "SLACK_AUTH_URI": "https://slack.com/oauth/v2/authorize",
        }
        client = for_service("slack", env=env)
        assert client.cfg.token_uri == "https://slack.com/api/oauth.token"
