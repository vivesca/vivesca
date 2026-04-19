"""Tests for mtor OAuth2 authentication module."""

import json
import time
from pathlib import Path

import pytest
from mtor.auth import (
    OAuth2Config,
    TokenInfo,
    TokenStore,
    client_credentials_flow,
    refresh_token,
)

# ---------------------------------------------------------------------------
# TokenInfo
# ---------------------------------------------------------------------------


class TestTokenInfo:
    def test_is_expired_false_when_no_expiry(self):
        token = TokenInfo(access_token="abc")
        assert token.is_expired is False

    def test_is_expired_false_when_future(self):
        token = TokenInfo(access_token="abc", expires_at=time.time() + 3600)
        assert token.is_expired is False

    def test_is_expired_true_when_past(self):
        token = TokenInfo(access_token="abc", expires_at=time.time() - 10)
        assert token.is_expired is True

    def test_is_expired_true_within_buffer(self):
        """Token within 60-second refresh buffer counts as expired."""
        token = TokenInfo(access_token="abc", expires_at=time.time() + 30)
        assert token.is_expired is True

    def test_to_dict_roundtrip(self):
        token = TokenInfo(
            access_token="abc123",
            token_type="Bearer",
            expires_at=1700000000.0,
            refresh_token="refresh_me",
            scope="read write",
        )
        data = token.to_dict()
        assert data["access_token"] == "abc123"
        assert data["refresh_token"] == "refresh_me"
        restored = TokenInfo.from_dict(data)
        assert restored.access_token == "abc123"
        assert restored.expires_at == 1700000000.0

    def test_from_dict_missing_optional_fields(self):
        data = {"access_token": "tok"}
        token = TokenInfo.from_dict(data)
        assert token.access_token == "tok"
        assert token.refresh_token is None
        assert token.scope == ""

    def test_is_valid_true(self):
        token = TokenInfo(access_token="abc", expires_at=time.time() + 3600)
        assert token.is_valid is True

    def test_is_valid_false_when_expired(self):
        token = TokenInfo(access_token="abc", expires_at=time.time() - 10)
        assert token.is_valid is False


# ---------------------------------------------------------------------------
# TokenStore
# ---------------------------------------------------------------------------


class TestTokenStore:
    def test_save_and_load(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        token = TokenInfo(access_token="tok1", expires_at=1700000000.0, refresh_token="rf1")
        store.save("my_provider", token)
        loaded = store.load("my_provider")
        assert loaded is not None
        assert loaded.access_token == "tok1"
        assert loaded.refresh_token == "rf1"

    def test_load_missing_provider(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        assert store.load("nonexistent") is None

    def test_load_missing_file(self, tmp_path: Path):
        store = TokenStore(tmp_path / "absent.json")
        assert store.load("anything") is None

    def test_delete(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        store.save("prov_a", TokenInfo(access_token="a"))
        store.save("prov_b", TokenInfo(access_token="b"))
        assert store.delete("prov_a") is True
        assert store.load("prov_a") is None
        assert store.load("prov_b") is not None

    def test_delete_nonexistent(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        assert store.delete("ghost") is False

    def test_file_permissions(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        store.save("prov", TokenInfo(access_token="secret"))
        mode = store.path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_overwrite_existing(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        store.save("prov", TokenInfo(access_token="old"))
        store.save("prov", TokenInfo(access_token="new"))
        loaded = store.load("prov")
        assert loaded is not None
        assert loaded.access_token == "new"

    def test_corrupt_file_returns_none(self, tmp_path: Path):
        token_file = tmp_path / "tokens.json"
        token_file.write_text("NOT VALID JSON{{{{")
        store = TokenStore(token_file)
        assert store.load("prov") is None

    def test_list_providers(self, tmp_path: Path):
        store = TokenStore(tmp_path / "tokens.json")
        store.save("alpha", TokenInfo(access_token="a"))
        store.save("beta", TokenInfo(access_token="b"))
        names = store.list_providers()
        assert sorted(names) == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# OAuth2Config
# ---------------------------------------------------------------------------


class TestOAuth2Config:
    def test_defaults(self):
        cfg = OAuth2Config(
            client_id="myapp",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
        )
        assert cfg.scopes == []
        assert cfg.redirect_port == 8400

    def test_custom_port_and_scopes(self):
        cfg = OAuth2Config(
            client_id="myapp",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"],
            redirect_port=9999,
        )
        assert cfg.scopes == ["read", "write"]
        assert cfg.redirect_port == 9999

    def test_redirect_uri(self):
        cfg = OAuth2Config(
            client_id="c",
            authorize_url="https://a",
            token_url="https://t",
            redirect_port=9090,
        )
        assert cfg.redirect_uri == "http://localhost:9090/callback"


# ---------------------------------------------------------------------------
# Client Credentials Flow
# ---------------------------------------------------------------------------


class TestClientCredentialsFlow:
    def test_success(self, monkeypatch, tmp_path):
        """Client credentials flow exchanges ID+secret for a token."""
        responses = [
            {
                "access_token": "cc_tok_123",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "read",
            }
        ]

        class FakeResponse:
            def __init__(self, data):
                self.status_code = 200
                self._data = data

            def read(self):
                return json.dumps(self._data).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        import urllib.request

        monkeypatch.setattr(
            urllib.request,
            "urlopen",
            lambda req, **kw: FakeResponse(responses.pop(0)),
        )

        cfg = OAuth2Config(
            client_id="test_client",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
        )
        token = client_credentials_flow(cfg, client_secret="s3cret")
        assert token.access_token == "cc_tok_123"
        assert token.token_type == "Bearer"
        assert not token.is_expired
        assert token.scope == "read"

    def test_server_error(self, monkeypatch):
        class FakeResponse:
            status_code = 401

            def read(self):
                return json.dumps({"error": "invalid_client"}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        import urllib.request

        monkeypatch.setattr(
            urllib.request,
            "urlopen",
            lambda req, **kw: (_ for _ in ()).throw(
                urllib.error.HTTPError("https://x", 401, "Unauthorized", {}, None)
            ),
        )
        import urllib.error

        cfg = OAuth2Config(
            client_id="bad",
            authorize_url="https://a",
            token_url="https://t",
        )
        with pytest.raises(OSError, match="401"):
            client_credentials_flow(cfg, client_secret="wrong")


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_success(self, monkeypatch):
        response_data = {
            "access_token": "new_access",
            "token_type": "Bearer",
            "expires_in": 7200,
            "refresh_token": "new_refresh",
        }

        class FakeResponse:
            def __init__(self):
                self.status_code = 200

            def read(self):
                return json.dumps(response_data).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: FakeResponse())

        cfg = OAuth2Config(
            client_id="test_client",
            authorize_url="https://a",
            token_url="https://t",
        )
        token = refresh_token(cfg, "old_refresh_token")
        assert token.access_token == "new_access"
        assert token.refresh_token == "new_refresh"
        assert not token.is_expired

    def test_refresh_failure_raises(self, monkeypatch):
        import urllib.error
        import urllib.request

        monkeypatch.setattr(
            urllib.request,
            "urlopen",
            lambda req, **kw: (_ for _ in ()).throw(
                urllib.error.HTTPError("https://x", 400, "Bad Request", {}, None)
            ),
        )

        cfg = OAuth2Config(client_id="c", authorize_url="https://a", token_url="https://t")
        with pytest.raises(OSError, match="400"):
            refresh_token(cfg, "bad_token")


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------


class TestPKCEHelpers:
    def test_generate_code_verifier(self):
        from mtor.auth import generate_code_verifier

        v1 = generate_code_verifier()
        v2 = generate_code_verifier()
        assert len(v1) >= 43
        assert v1 != v2  # should be random

    def test_generate_code_challenge(self):
        from mtor.auth import generate_code_challenge

        verifier = "abc123_verifier_string_that_is_long_enough_for_s256"
        challenge = generate_code_challenge(verifier)
        assert len(challenge) > 0
        # S256 challenge should be different from verifier
        assert challenge != verifier

    def test_build_authorize_url(self):
        from mtor.auth import build_authorize_url

        cfg = OAuth2Config(
            client_id="myapp",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"],
        )
        url = build_authorize_url(cfg, "code_challenge_xyz", "S256", state="mystate")
        assert "client_id=myapp" in url
        assert "code_challenge=code_challenge_xyz" in url
        assert "code_challenge_method=S256" in url
        assert "scope=read+write" in url
        assert "state=mystate" in url
        assert "response_type=code" in url


# ---------------------------------------------------------------------------
# get_token — integration-style test
# ---------------------------------------------------------------------------


class TestGetToken:
    def test_valid_token_returned_directly(self, tmp_path):
        from mtor.auth import TokenStore, get_token

        store = TokenStore(tmp_path / "tokens.json")
        future = time.time() + 3600
        store.save("prov", TokenInfo(access_token="valid_tok", expires_at=future))

        token = get_token("prov", store)
        assert token == "valid_tok"

    def test_refreshes_expired_token(self, tmp_path, monkeypatch):
        from mtor.auth import TokenStore, get_token

        store = TokenStore(tmp_path / "tokens.json")
        past = time.time() - 10
        store.save(
            "prov",
            TokenInfo(
                access_token="expired_tok",
                expires_at=past,
                refresh_token="rt_123",
            ),
        )

        # Mock the refresh to return a new token
        new_response = {
            "access_token": "refreshed_tok",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new_rt",
        }

        class FakeResponse:
            status_code = 200

            def read(self):
                return json.dumps(new_response).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: FakeResponse())

        cfg = OAuth2Config(
            client_id="c",
            authorize_url="https://a",
            token_url="https://t",
        )
        token = get_token("prov", store, oauth2_config=cfg)
        assert token == "refreshed_tok"

    def test_returns_none_when_no_token(self, tmp_path):
        from mtor.auth import TokenStore, get_token

        store = TokenStore(tmp_path / "tokens.json")
        assert get_token("missing", store) is None

    def test_returns_none_when_expired_no_refresh(self, tmp_path):
        from mtor.auth import TokenStore, get_token

        store = TokenStore(tmp_path / "tokens.json")
        store.save(
            "prov",
            TokenInfo(access_token="old", expires_at=time.time() - 100),
        )
        assert get_token("prov", store) is None


# ---------------------------------------------------------------------------
# CLI auth commands (integration-level)
# ---------------------------------------------------------------------------


class TestAuthLoginCommand:
    def test_client_credentials_login(self, monkeypatch, tmp_path):
        """Client-credentials login stores token and prints JSON."""
        from mtor.auth import TokenStore

        token_path = tmp_path / "tokens.json"
        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(token_path))

        response_data = {
            "access_token": "cc_tok_cli",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        class FakeResponse:
            status_code = 200

            def read(self):
                return json.dumps(response_data).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: FakeResponse())

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(
                [
                    "auth",
                    "login",
                    "-p",
                    "my_prov",
                    "--client-id",
                    "cid",
                    "--token-url",
                    "https://tok",
                    "--client-secret",
                    "sec",
                ]
            )
        assert exc_info.value.code == 0

        store = TokenStore(token_path)
        tok = store.load("my_prov")
        assert tok is not None
        assert tok.access_token == "cc_tok_cli"

    def test_login_missing_both_flows(self, monkeypatch, tmp_path, capsys):
        """Login without --authorize-url or --client-secret exits with error."""
        from mtor.auth import TokenStore

        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(tmp_path / "tokens.json"))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "login", "-p", "x", "--client-id", "c", "--token-url", "https://t"])
        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "Provide --authorize-url" in output


class TestAuthStatusCommand:
    def test_status_no_providers(self, monkeypatch, tmp_path, capsys):
        from mtor.auth import TokenStore

        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(tmp_path / "tokens.json"))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "status"])
        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["authenticated_providers"] == []

    def test_status_with_provider(self, monkeypatch, tmp_path, capsys):
        from mtor.auth import TokenInfo, TokenStore

        token_path = tmp_path / "tokens.json"
        store = TokenStore(token_path)
        store.save(
            "demo",
            TokenInfo(access_token="tok", expires_at=time.time() + 3600, refresh_token="rt"),
        )
        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(token_path))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "status", "-p", "demo"])
        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["authenticated"] is True
        assert data["expired"] is False

    def test_status_all_providers(self, monkeypatch, tmp_path, capsys):
        from mtor.auth import TokenInfo, TokenStore

        token_path = tmp_path / "tokens.json"
        store = TokenStore(token_path)
        store.save("a", TokenInfo(access_token="ta"))
        store.save("b", TokenInfo(access_token="tb"))
        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(token_path))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "status"])
        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert len(data["authenticated_providers"]) == 2


class TestAuthLogoutCommand:
    def test_logout_existing(self, monkeypatch, tmp_path, capsys):
        from mtor.auth import TokenInfo, TokenStore

        token_path = tmp_path / "tokens.json"
        store = TokenStore(token_path)
        store.save("prov", TokenInfo(access_token="tok"))
        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(token_path))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "logout", "-p", "prov"])
        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["ok"] is True
        assert store.load("prov") is None

    def test_logout_nonexistent(self, monkeypatch, tmp_path, capsys):
        from mtor.auth import TokenStore

        monkeypatch.setattr("mtor.cli.TokenStore", lambda: TokenStore(tmp_path / "tokens.json"))

        from mtor.cli import app

        with pytest.raises(SystemExit) as exc_info:
            app(["auth", "logout", "-p", "ghost"])
        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["ok"] is False
