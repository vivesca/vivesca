from __future__ import annotations

"""gmail — Gmail API client for headless environments.

Biology: the peroxisome processes and detoxifies cargo. Here, the Gmail
client handles raw API calls — auth, fetch, modify — so higher-level
organelles (endosomal) can focus on classification logic.

Auth: uses refresh token from env vars (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET,
GMAIL_REFRESH_TOKEN) or falls back to gog's token.json file. No browser needed
after initial setup.
"""

import base64
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GOG_TOKEN_FILE = Path.home() / ".config" / "gog" / "token.json"


def _get_credentials() -> Credentials:
    """Build credentials from env vars or gog token file.

    Priority:
    1. Env vars: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
    2. gog's cached token.json (backwards compat)
    """
    client_id = os.environ.get("GMAIL_CLIENT_ID", "")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN", "")

    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=GMAIL_SCOPES,
        )
        creds.refresh(Request())
        return creds

    if GOG_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GOG_TOKEN_FILE), GMAIL_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if creds and creds.valid:
            return creds

    raise RuntimeError(
        "Gmail auth failed. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, "
        "GMAIL_REFRESH_TOKEN env vars, or place a valid token.json at "
        f"{GOG_TOKEN_FILE}"
    )


@lru_cache(maxsize=1)
def service():
    """Return an authenticated Gmail API service (cached)."""
    return build("gmail", "v1", credentials=_get_credentials())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _header(msg: dict, name: str) -> str:
    for header in msg.get("payload", {}).get("headers", []):
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def _date_str(msg: dict) -> str:
    ts = int(msg.get("internalDate", 0)) / 1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""


def _decode_body(payload: dict) -> str:
    """Decode message body from base64url, preferring text/plain. Recurses into nested multipart."""
    def _find_part(node: dict, mime: str) -> str:
        if node.get("mimeType") == mime:
            data = node.get("body", {}).get("data", "")
            if data:
                return data
        for part in node.get("parts", []):
            found = _find_part(part, mime)
            if found:
                return found
        return ""

    body_data = _find_part(payload, "text/plain") or _find_part(payload, "text/html")
    if not body_data:
        return ""
    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")


def _format_message(msg: dict, include_body: bool = False) -> str:
    """Format a message dict into a readable string."""
    msg_id = msg.get("id", "")
    date = _date_str(msg)
    sender = _header(msg, "From")
    subject = _header(msg, "Subject")
    snippet = msg.get("snippet", "")
    line = f"{msg_id}  {date} | {sender} | {subject} | {snippet}"
    if include_body:
        body = _decode_body(msg.get("payload", {}))
        line += f"\n---\n{body}\n---"
    return line


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def search(query: str, max_results: int = 20) -> str:
    """Search Gmail. Returns formatted message list."""
    svc = service()
    result = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = result.get("messages", [])
    if not messages:
        return "No messages found."
    lines = []
    for msg_stub in messages:
        msg = svc.users().messages().get(
            userId="me", id=msg_stub["id"], format="metadata"
        ).execute()
        lines.append(_format_message(msg))
    return "\n".join(lines)


def get_thread(thread_id: str) -> str:
    """Get full thread content."""
    svc = service()
    thread = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = thread.get("messages", [])
    lines = []
    for msg in messages:
        lines.append(_format_message(msg, include_body=True))
    return "\n\n".join(lines)


def get_message(message_id: str, full: bool = True) -> str:
    """Get a single message."""
    svc = service()
    fmt = "full" if full else "metadata"
    msg = svc.users().messages().get(userId="me", id=message_id, format=fmt).execute()
    return _format_message(msg, include_body=full)


def archive(message_ids: list[str]) -> str:
    """Archive messages (remove INBOX label)."""
    svc = service()
    for msg_id in message_ids:
        svc.users().messages().modify(
            userId="me", id=msg_id,
            body={"removeLabelIds": ["INBOX"]}
        ).execute()
    return f"Archived {len(message_ids)} message(s)."


def mark_read(message_ids: list[str]) -> str:
    """Mark messages as read (remove UNREAD label)."""
    svc = service()
    for msg_id in message_ids:
        svc.users().messages().modify(
            userId="me", id=msg_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    return f"Marked {len(message_ids)} message(s) as read."


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    reply_to_message_id: str = "",
    attachments: list[str] | None = None,
) -> str:
    """Send an email or reply to a thread."""
    svc = service()

    msg_mime = MIMEText(body) if not attachments else MIMEMultipart()
    if attachments:
        msg_mime.attach(MIMEText(body))

    msg_mime["to"] = to
    msg_mime["subject"] = subject
    if cc:
        msg_mime["cc"] = cc

    raw = base64.urlsafe_b64encode(msg_mime.as_bytes()).decode()
    send_body: dict = {"raw": raw}

    if reply_to_message_id:
        original = svc.users().messages().get(
            userId="me", id=reply_to_message_id, format="metadata"
        ).execute()
        thread_id = original.get("threadId", "")
        if thread_id:
            send_body["threadId"] = thread_id
        msg_id_header = _header(original, "Message-ID")
        refs = _header(original, "References")
        if msg_id_header:
            new_refs = f"{refs} {msg_id_header}".strip() if refs else msg_id_header
            msg_mime["In-Reply-To"] = msg_id_header
            msg_mime["References"] = new_refs
            send_body["raw"] = base64.urlsafe_b64encode(msg_mime.as_bytes()).decode()

    result = svc.users().messages().send(userId="me", body=send_body).execute()
    return f"Sent. Message ID: {result.get('id', 'unknown')}"


def list_labels() -> str:
    """List all Gmail labels."""
    svc = service()
    result = svc.users().labels().list(userId="me").execute()
    labels = result.get("labels", [])
    return "\n".join(f"{label['id']}: {label['name']}" for label in labels)


def create_label(name: str) -> str:
    """Create a Gmail label."""
    svc = service()
    result = svc.users().labels().create(
        userId="me",
        body={"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
    ).execute()
    return f"Created label: {result['name']} (id: {result['id']})"


def create_filter(
    from_sender: str = "",
    subject_pattern: str = "",
    add_label: str = "",
    archive: bool = False,
    mark_read: bool = False,
) -> str:
    """Create a Gmail filter."""
    svc = service()
    criteria: dict = {}
    if from_sender:
        criteria["from"] = from_sender
    if subject_pattern:
        criteria["subject"] = subject_pattern

    action: dict = {}
    if add_label:
        labels = svc.users().labels().list(userId="me").execute().get("labels", [])
        label_id = next((label["id"] for label in labels if label["name"] == add_label), None)
        if label_id:
            action["addLabelIds"] = [label_id]
    if archive:
        action["removeLabelIds"] = action.get("removeLabelIds", []) + ["INBOX"]
    if mark_read:
        action["removeLabelIds"] = action.get("removeLabelIds", []) + ["UNREAD"]

    result = svc.users().settings().filters().create(
        userId="me",
        body={"criteria": criteria, "action": action},
    ).execute()
    return f"Filter created: {result.get('id', 'unknown')}"
