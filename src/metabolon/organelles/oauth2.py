"""oauth2 — centralized OAuth2 authentication for metabolon organelles.

Biology: the nuclear pore regulates transport between nucleus and cytoplasm.
Here, the OAuth2 module controls the flow of credentials: issuing authorization
requests, exchanging codes for tokens, refreshing expired tokens, and revoking
access — so individual organelles (gmail, calendar, etc.) don't each roll their
own auth logic.

Supports:
  - Authorization Code flow with PKCE (recommended for CLI/headless)
  - Automatic token refresh when expired
  - Per-service token isolation
  - Token persistence to ~/.config/vivesca/oauth2/<service>.json

Usage:
    from metabolon.organelles.oauth2 import for_service

    client = for_service("gmail")
    url, state, verifier = client.authorization_url()
    # ... user visits url, grants access, returns code ...
    token = client.exchange_code(code, code_verifier=verifier)
    header = client.get_auth_header()  # {"Authorization": "Bearer <at>"}
"""

import contextlib
import hashlib
import json
import os
import secrets
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx

# Default token storage location
_DEFAULT_STORE_DIR = Path.home() / ".config" / "vivesca" / "oauth2"

# Buffer seconds before actual expiry to trigger early refresh
_EXPIRY_BUFFER = 60

# Default OAuth2 endpoints (Google)
_DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
_DEFAULT_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
_DEFAULT_REVOKE_URI = "https://oauth2.googleapis.com/revoke"


# ---------------------------------------------------------------------------
# TokenStore — persistence layer
# ---------------------------------------------------------------------------


class TokenStore:
    """File-backed token storage. Each service gets its own JSON file."""

    def __init__(self, base_dir: Path) -> None:
        self._dir = Path(base_dir)

    def _path(self, service: str) -> Path:
        return self._dir / f"{service}.json"

    def save(self, service: str, token: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(service).write_text(json.dumps(token, indent=2))

    def load(self, service: str) -> dict[str, Any] | None:
        p = self._path(service)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def delete(self, service: str) -> None:
        p = self._path(service)
        if p.exists():
            p.unlink()


# ---------------------------------------------------------------------------
# OAuth2Config — service configuration
# ---------------------------------------------------------------------------


class OAuth2Config:
    """Configuration for an OAuth2 provider."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_uri: str = _DEFAULT_TOKEN_URI,
        auth_uri: str = _DEFAULT_AUTH_URI,
        scopes: list[str] | None = None,
        redirect_uri: str = "http://localhost:8080/callback",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_uri = token_uri
        self.auth_uri = auth_uri
        self.scopes = scopes or []
        self.redirect_uri = redirect_uri

    @classmethod
    def from_env(
        cls,
        prefix: str,
        env: dict[str, str] | None = None,
    ) -> "OAuth2Config":
        """Build config from environment variables with a given prefix.

        Reads: <PREFIX>_CLIENT_ID, <PREFIX>_CLIENT_SECRET, <PREFIX>_SCOPES,
               <PREFIX>_TOKEN_URI, <PREFIX>_AUTH_URI, <PREFIX>_REDIRECT_URI.

        All except CLIENT_ID and CLIENT_SECRET have sensible defaults.
        """
        source = env if env is not None else os.environ
        upper = prefix.upper()

        client_id = source.get(f"{upper}_CLIENT_ID", "")
        client_secret = source.get(f"{upper}_CLIENT_SECRET", "")
        if not client_id:
            raise ValueError(
                f"{upper}_CLIENT_ID is required for OAuth2 config (prefix={prefix!r})"
            )

        scopes_raw = source.get(f"{upper}_SCOPES", "")
        scopes = scopes_raw.split() if scopes_raw else []

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            token_uri=source.get(f"{upper}_TOKEN_URI", _DEFAULT_TOKEN_URI),
            auth_uri=source.get(f"{upper}_AUTH_URI", _DEFAULT_AUTH_URI),
            scopes=scopes,
            redirect_uri=source.get(f"{upper}_REDIRECT_URI", "http://localhost:8080/callback"),
        )


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256).

    Returns (verifier, challenge).
    """
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = __import__("base64").urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# ---------------------------------------------------------------------------
# OAuth2Client — main client
# ---------------------------------------------------------------------------


class OAuth2Client:
    """High-level OAuth2 client with token management.

    Args:
        cfg: OAuth2 provider configuration.
        store_dir: Directory for token persistence.
        service: Service name for token file isolation.
    """

    def __init__(
        self,
        cfg: OAuth2Config,
        store_dir: Path | None = None,
        service: str = "default",
    ) -> None:
        self.cfg = cfg
        self.store = TokenStore(store_dir or _DEFAULT_STORE_DIR)
        self._service = service

    # -- Authorization URL ---------------------------------------------------

    def authorization_url(
        self,
        state: str | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> tuple[str, str, str]:
        """Build the authorization URL with PKCE.

        Returns:
            (url, state, code_verifier) — store the verifier for the callback.
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        verifier, challenge = _generate_pkce()

        params = {
            "client_id": self.cfg.client_id,
            "redirect_uri": self.cfg.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.cfg.scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
        if extra_params:
            params.update(extra_params)

        url = f"{self.cfg.auth_uri}?{urllib.parse.urlencode(params)}"
        return url, state, verifier

    # -- Token exchange ------------------------------------------------------

    def exchange_code(
        self,
        code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """Exchange an authorization code for tokens.

        Saves the resulting token to the store and returns it.
        Raises RuntimeError on HTTP errors.
        """
        resp = httpx.post(
            self.cfg.token_uri,
            data={
                "client_id": self.cfg.client_id,
                "client_secret": self.cfg.client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": self.cfg.redirect_uri,
            },
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Token exchange failed (HTTP {resp.status_code}): {resp.text}")

        token_data = resp.json()
        token = _normalise_token(token_data)
        self.store.save(self._service, token)
        return token

    # -- Token refresh -------------------------------------------------------

    def refresh(self) -> dict[str, Any]:
        """Refresh the stored access token using the refresh token.

        Returns the updated token dict. Raises RuntimeError if no refresh
        token is available or the server rejects the request.
        """
        current = self.store.load(self._service)
        if current is None:
            raise RuntimeError("No saved token to refresh")

        refresh_token = current.get("refresh_token", "")
        if not refresh_token:
            raise RuntimeError("Saved token has no refresh_token")

        resp = httpx.post(
            self.cfg.token_uri,
            data={
                "client_id": self.cfg.client_id,
                "client_secret": self.cfg.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Token refresh failed (HTTP {resp.status_code}): {resp.text}")

        new_data = resp.json()
        # Preserve refresh_token if the server doesn't return one
        if "refresh_token" not in new_data:
            new_data["refresh_token"] = refresh_token

        token = _normalise_token(new_data)
        self.store.save(self._service, token)
        return token

    # -- Get valid token (auto-refresh) --------------------------------------

    def get_valid_token(self) -> dict[str, Any]:
        """Return a valid (unexpired) token, refreshing if necessary.

        Raises RuntimeError if no token exists and cannot be refreshed.
        """
        token = self.store.load(self._service)
        if token is None:
            raise RuntimeError("No saved token — run authorization flow first")

        if _is_expired(token):
            token = self.refresh()

        return token

    # -- Convenience ----------------------------------------------------------

    def get_auth_header(self) -> dict[str, str]:
        """Return an Authorization header dict with the current bearer token."""
        token = self.get_valid_token()
        return {"Authorization": f"Bearer {token['access_token']}"}

    # -- Revoke --------------------------------------------------------------

    def revoke(self) -> None:
        """Revoke the stored token and delete it from the store."""
        token = self.store.load(self._service)
        if token is None:
            return

        revoke_uri = _DEFAULT_REVOKE_URI
        with contextlib.suppress(Exception):
            httpx.post(revoke_uri, data={"token": token.get("access_token", "")})

        self.store.delete(self._service)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_token(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert expires_in → expires_at for consistent expiry checks."""
    token = dict(raw)
    if "expires_in" in token:
        token["expires_at"] = time.time() + token.pop("expires_in")
    return token


def _is_expired(token: dict[str, Any]) -> bool:
    """Check if a token is expired (with buffer)."""
    expires_at = token.get("expires_at", 0)
    return time.time() >= (expires_at - _EXPIRY_BUFFER)


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


def for_service(
    prefix: str,
    env: dict[str, str] | None = None,
    store_dir: Path | None = None,
) -> OAuth2Client:
    """Create an OAuth2Client from environment variables.

    Args:
        prefix: Env var prefix, e.g. "gmail" reads GMAIL_CLIENT_ID.
        env: Override os.environ (for testing).
        store_dir: Override default token store directory.
    """
    cfg = OAuth2Config.from_env(prefix, env=env)
    return OAuth2Client(
        cfg,
        store_dir=store_dir,
        service=prefix.lower(),
    )
