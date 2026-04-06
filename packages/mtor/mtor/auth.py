"""OAuth2 authentication — token acquisition, refresh, and secure storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TOKEN_PATH = Path.home() / ".config" / "mtor" / "tokens.json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class OAuth2Config:
    """OAuth2 provider endpoints and credentials."""

    client_id: str
    authorize_url: str
    token_url: str
    scopes: list[str] = field(default_factory=list)
    redirect_port: int = 8400

    @property
    def redirect_uri(self) -> str:
        return f"http://localhost:{self.redirect_port}/callback"


@dataclass
class TokenInfo:
    """A stored OAuth2 access/refresh token pair."""

    access_token: str
    token_type: str = "Bearer"
    expires_at: float = 0.0
    refresh_token: str | None = None
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        # Refresh 60 seconds early to avoid edge-case failures.
        return time.time() >= self.expires_at - 60

    @property
    def is_valid(self) -> bool:
        return not self.is_expired

    def to_dict(self) -> dict:
        d: dict = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at,
        }
        if self.refresh_token is not None:
            d["refresh_token"] = self.refresh_token
        if self.scope:
            d["scope"] = self.scope
        return d

    @classmethod
    def from_dict(cls, data: dict) -> TokenInfo:
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=data.get("expires_at", 0.0),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope", ""),
        )


# ---------------------------------------------------------------------------
# Token store (file-backed, permission-restricted)
# ---------------------------------------------------------------------------


class TokenStore:
    """Secure file-based token storage for multiple providers."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_TOKEN_PATH

    def _read_all(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        # Restrict to owner-only (rw-------).
        self.path.chmod(0o600)

    def save(self, provider: str, token: TokenInfo) -> None:
        all_tokens = self._read_all()
        all_tokens[provider] = token.to_dict()
        self._write_all(all_tokens)

    def load(self, provider: str) -> TokenInfo | None:
        all_tokens = self._read_all()
        entry = all_tokens.get(provider)
        if entry is None:
            return None
        return TokenInfo.from_dict(entry)

    def delete(self, provider: str) -> bool:
        all_tokens = self._read_all()
        if provider not in all_tokens:
            return False
        del all_tokens[provider]
        self._write_all(all_tokens)
        return True

    def list_providers(self) -> list[str]:
        return list(self._read_all().keys())


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random PKCE code verifier."""
    raw = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_code_challenge(verifier: str) -> str:
    """Produce an S256 PKCE code challenge from a verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_authorize_url(
    config: OAuth2Config,
    code_challenge: str,
    code_challenge_method: str = "S256",
    state: str | None = None,
) -> str:
    """Build the full authorization URL with PKCE parameters."""
    params: dict[str, str] = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
    }
    if config.scopes:
        params["scope"] = " ".join(config.scopes)
    if state:
        params["state"] = state
    separator = "&" if "?" in config.authorize_url else "?"
    return config.authorize_url + separator + urllib.parse.urlencode(params)


# ---------------------------------------------------------------------------
# Token exchange helpers
# ---------------------------------------------------------------------------


def _parse_token_response(response_data: dict) -> TokenInfo:
    """Parse a token endpoint JSON response into a TokenInfo."""
    expires_in = response_data.get("expires_in", 0)
    expires_at = time.time() + expires_in if expires_in else 0.0
    return TokenInfo(
        access_token=response_data["access_token"],
        token_type=response_data.get("token_type", "Bearer"),
        expires_at=expires_at,
        refresh_token=response_data.get("refresh_token"),
        scope=response_data.get("scope", ""),
    )


def _post_token_request(url: str, body: dict) -> TokenInfo:
    """POST a form-encoded body to a token endpoint and return TokenInfo."""
    encoded = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise OSError(
            f"Token request failed: HTTP {exc.code} — {exc.reason}"
        ) from exc
    return _parse_token_response(data)


# ---------------------------------------------------------------------------
# Flows
# ---------------------------------------------------------------------------


def client_credentials_flow(config: OAuth2Config, client_secret: str) -> TokenInfo:
    """Perform OAuth2 Client Credentials grant."""
    body: dict[str, str] = {
        "grant_type": "client_credentials",
        "client_id": config.client_id,
        "client_secret": client_secret,
    }
    if config.scopes:
        body["scope"] = " ".join(config.scopes)
    return _post_token_request(config.token_url, body)


def refresh_token(config: OAuth2Config, refresh: str) -> TokenInfo:
    """Refresh an access token using a refresh token."""
    body: dict[str, str] = {
        "grant_type": "refresh_token",
        "client_id": config.client_id,
        "refresh_token": refresh,
    }
    return _post_token_request(config.token_url, body)


def authorization_code_flow(
    config: OAuth2Config,
    code: str,
    code_verifier: str,
) -> TokenInfo:
    """Exchange an authorization code (with PKCE verifier) for tokens."""
    body: dict[str, str] = {
        "grant_type": "authorization_code",
        "client_id": config.client_id,
        "code": code,
        "redirect_uri": config.redirect_uri,
        "code_verifier": code_verifier,
    }
    return _post_token_request(config.token_url, body)


# ---------------------------------------------------------------------------
# High-level token retrieval
# ---------------------------------------------------------------------------


def get_token(
    provider_name: str,
    store: TokenStore,
    oauth2_config: OAuth2Config | None = None,
) -> str | None:
    """Return a valid access token for *provider_name*.

    Returns the token string, or ``None`` if no token exists and cannot be
    obtained.  If a stored token is expired but has a refresh_token, it will
    be refreshed automatically (requires *oauth2_config*).
    """
    token = store.load(provider_name)
    if token is None:
        return None
    if token.is_valid:
        return token.access_token
    # Attempt refresh.
    if token.refresh_token and oauth2_config is not None:
        try:
            new_token = refresh_token(oauth2_config, token.refresh_token)
            store.save(provider_name, new_token)
            return new_token.access_token
        except OSError:
            return None
    return None
