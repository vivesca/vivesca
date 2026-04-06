"""google_auth — shared Google OAuth2 credential management.

Eliminates duplicated auth logic across circadian_clock and gmail organelles.
Provides a single get_credentials() entry point that:

1. Reads credentials from env vars (configurable prefix, default GOOGLE_)
2. Falls back to a gog-style token.json file
3. Handles refresh transparently
4. Raises a clear RuntimeError when nothing works

Usage:
    from metabolon.organelles.google_auth import get_credentials, build_service

    creds = get_credentials(scopes=CALENDAR_SCOPES)
    service = build_service("calendar", "v3", scopes=CALENDAR_SCOPES)
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TOKEN_FILE = Path.home() / ".config" / "gog" / "token.json"

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


def get_credentials(
    *,
    scopes: list[str],
    env_prefix: str = "GOOGLE",
    token_file: Path | None = None,
) -> Credentials:
    """Return valid Google OAuth2 credentials.

    Resolution order:
    1. Env vars: {PREFIX}_CLIENT_ID, {PREFIX}_CLIENT_SECRET, {PREFIX}_REFRESH_TOKEN
    2. Token file (gog token.json format)

    Args:
        scopes: OAuth2 scopes to request.
        env_prefix: Prefix for env var names (default: GOOGLE).
        token_file: Path to a gog-style token.json. Defaults to ~/.config/gog/token.json.

    Returns:
        Valid, refreshed Credentials object.

    Raises:
        RuntimeError: No credentials available from any source.
    """
    if token_file is None:
        token_file = DEFAULT_TOKEN_FILE

    # --- Path 1: environment variables ---
    client_id = os.environ.get(f"{env_prefix}_CLIENT_ID", "")
    client_secret = os.environ.get(f"{env_prefix}_CLIENT_SECRET", "")
    refresh_token = os.environ.get(f"{env_prefix}_REFRESH_TOKEN", "")

    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
        )
        creds.refresh(Request())
        return creds

    # --- Path 2: token file ---
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
        if not creds:
            pass  # fall through to error
        elif creds.expired and creds.refresh_token:
            creds.refresh(Request())
            return creds  # refresh succeeded — trust it
        elif creds.valid:
            return creds

    raise RuntimeError(
        f"Google auth failed. Set {env_prefix}_CLIENT_ID, {env_prefix}_CLIENT_SECRET, "
        f"{env_prefix}_REFRESH_TOKEN env vars, or place a valid token.json at {token_file}"
    )


# ---------------------------------------------------------------------------
# Convenience: build an authenticated API service
# ---------------------------------------------------------------------------


def build_service(
    *,
    api: str,
    version: str,
    scopes: list[str],
    env_prefix: str = "GOOGLE",
    token_file: Path | None = None,
):
    """Return an authenticated Google API service object.

    Wraps get_credentials() + googleapiclient.discovery.build().

    Args:
        api: API name (e.g. "calendar", "gmail").
        version: API version string (e.g. "v3", "v1").
        scopes: OAuth2 scopes to request.
        env_prefix: Prefix for env var names (default: GOOGLE).
        token_file: Path to a gog-style token.json.

    Returns:
        Authenticated Google API service object.
    """
    creds = get_credentials(
        scopes=scopes,
        env_prefix=env_prefix,
        token_file=token_file,
    )
    return build(api, version, credentials=creds)
