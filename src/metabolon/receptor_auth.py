"""receptor_auth — centralized OAuth2 credential management.

Biology: cell-surface receptors must authenticate external signals before
the cell responds. This module is the ligand-recognition domain — it
validates credentials so that organelles (gmail, circadian_clock, etc.)
can focus on their domain logic.

Supports Google OAuth2 with two credential sources:
1. Environment variables: {PREFIX}_CLIENT_ID, {PREFIX}_CLIENT_SECRET, {PREFIX}_REFRESH_TOKEN
2. Token file: a JSON file with authorized_user credentials (gog compat)

Env vars take priority. Token file is the fallback.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OAuth2Config:
    """Configuration for an OAuth2 credential source.

    Attributes:
        prefix: Environment variable prefix (e.g., "GMAIL", "GCAL").
        scopes: OAuth2 scopes required for the target API.
        token_file: Optional path to a token JSON file. Falls back to
                    the default gog token file if not set.
        token_uri: OAuth2 token endpoint URI.
    """

    prefix: str
    scopes: list[str] = field(default_factory=list)
    token_file: Path | None = None
    token_uri: str = "https://oauth2.googleapis.com/token"

    # Default token file location (gog compatibility)
    _DEFAULT_TOKEN_DIR = Path.home() / ".config" / "gog"
    _DEFAULT_TOKEN_FILE = _DEFAULT_TOKEN_DIR / "token.json"

    @property
    def env_client_id(self) -> str:
        return os.environ.get(f"{self.prefix}_CLIENT_ID", "")

    @property
    def env_client_secret(self) -> str:
        return os.environ.get(f"{self.prefix}_CLIENT_SECRET", "")

    @property
    def env_refresh_token(self) -> str:
        return os.environ.get(f"{self.prefix}_REFRESH_TOKEN", "")

    @property
    def has_env_credentials(self) -> bool:
        return bool(self.env_client_id and self.env_client_secret and self.env_refresh_token)

    @property
    def resolved_token_file(self) -> Path:
        """Return the configured token file, or the default gog location."""
        return self.token_file or self._DEFAULT_TOKEN_FILE


def get_google_credentials(config: OAuth2Config) -> Credentials:
    """Build Google OAuth2 credentials from env vars or token file.

    Priority:
    1. Environment variables ({PREFIX}_CLIENT_ID, _CLIENT_SECRET, _REFRESH_TOKEN)
    2. Token file (config.token_file or default gog location)

    Raises:
        RuntimeError: if no valid credential source is found.
    """
    # --- Path 1: environment variables ---
    if config.has_env_credentials:
        creds = Credentials(
            token=None,
            refresh_token=config.env_refresh_token,
            client_id=config.env_client_id,
            client_secret=config.env_client_secret,
            token_uri=config.token_uri,
            scopes=config.scopes,
        )
        creds.refresh(Request())
        return creds

    # --- Path 2: token file ---
    token_path = config.resolved_token_file
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), config.scopes)
        if creds:
            if creds.valid:
                return creds
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                return creds

    raise RuntimeError(
        f"{config.prefix} auth failed. Set {config.prefix}_CLIENT_ID, "
        f"{config.prefix}_CLIENT_SECRET, {config.prefix}_REFRESH_TOKEN "
        f"env vars, or place a valid token.json at {token_path}"
    )


def get_credential_status(config: OAuth2Config) -> dict[str, str | bool | list[str] | None]:
    """Check credential availability without raising.

    Returns a status dict with keys:
        available: bool — credentials are obtainable
        source: "env_vars" | "token_file" | None — where they came from
        prefix: str — the configured prefix
        scopes: list[str] — required scopes
        error: str | None — error message if unavailable
    """
    # Check env vars first
    if config.has_env_credentials:
        try:
            get_google_credentials(config)
            return {
                "available": True,
                "source": "env_vars",
                "prefix": config.prefix,
                "scopes": config.scopes,
                "error": None,
            }
        except Exception as exc:
            logger.debug("Env credential check failed for %s: %s", config.prefix, exc)

    # Check token file
    token_path = config.resolved_token_file
    if token_path.exists():
        try:
            get_google_credentials(config)
            return {
                "available": True,
                "source": "token_file",
                "prefix": config.prefix,
                "scopes": config.scopes,
                "error": None,
            }
        except Exception as exc:
            logger.debug("File credential check failed for %s: %s", config.prefix, exc)

    return {
        "available": False,
        "source": None,
        "prefix": config.prefix,
        "scopes": config.scopes,
        "error": (
            f"No credentials found. Set {config.prefix}_CLIENT_ID, "
            f"{config.prefix}_CLIENT_SECRET, {config.prefix}_REFRESH_TOKEN "
            f"env vars, or place a valid token.json at {token_path}"
        ),
    }
