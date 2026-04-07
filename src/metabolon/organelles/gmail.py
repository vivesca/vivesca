"""gmail — Gmail API client for headless environments.

Biology: the peroxisome processes and detoxifies cargo. Here, the Gmail
client handles raw API calls — auth, fetch, modify — so higher-level
organelles (endosomal) can focus on classification logic.

Auth: uses centralized receptor_auth module with refresh token from env vars
(GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN) or falls back to
gog's token.json file. No browser needed after initial setup.
"""

import base64
import html
import mimetypes
import re
from datetime import datetime
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest

from metabolon.receptor_auth import OAuth2Config, get_google_credentials

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
_AUTH_CONFIG = OAuth2Config(prefix="GMAIL", scopes=GMAIL_SCOPES)


def _get_credentials():
    """Build credentials from env vars or gog token file via receptor_auth."""
    return get_google_credentials(_AUTH_CONFIG)


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


def _strip_html(html_text: str) -> str:
    """Strip HTML tags, removing <style>/<script> blocks and preserving line breaks."""
    # 1. Remove <style>...</style> and <script>...</script> blocks entirely
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # 2. Replace block-closing / line-break tags with newlines before stripping
    text = re.sub(r"<br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div|tr)>", "\n", text, flags=re.IGNORECASE)
    # 3. Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # 4. Unescape HTML entities
    text = html.unescape(text)
    # 5. Collapse runs of whitespace (excluding newlines) and limit consecutive newlines to 2
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode_body(payload: dict) -> str:
    """Decode message body from base64url, preferring text/plain. Recurses into nested multipart."""

    def _find_part(node: dict, mime: str) -> str | None:
        if node.get("mimeType") == mime:
            data = node.get("body", {}).get("data", "")
            if data:
                return data
        for part in node.get("parts", []):
            found = _find_part(part, mime)
            if found:
                return found
        return None

    plain_data = _find_part(payload, "text/plain")
    if plain_data:
        return base64.urlsafe_b64decode(plain_data).decode("utf-8", errors="replace")

    html_data = _find_part(payload, "text/html")
    if html_data:
        raw = base64.urlsafe_b64decode(html_data).decode("utf-8", errors="replace")
        return _strip_html(raw)

    return ""


def _format_message(msg: dict, include_body: bool = False) -> str:
    """Format a message dict into a readable string."""
    msg_id = msg.get("id", "")
    thread_id = msg.get("threadId", "")
    date = _date_str(msg)
    sender = _header(msg, "From")
    subject = _header(msg, "Subject")
    snippet = msg.get("snippet", "")
    thread_tag = f" [thread:{thread_id}]" if thread_id and thread_id != msg_id else ""
    line = f"{msg_id}{thread_tag}  {date} | {sender} | {subject} | {snippet}"
    if include_body:
        body = _decode_body(msg.get("payload", {}))
        line += f"\n---\n{body}\n---"
    return line


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def search(query: str, max_results: int = 20, threads: bool = False) -> str:
    """Search Gmail. Returns formatted message list.

    Uses batch API (up to 100 per batch) instead of N+1 individual get() calls.
    Supports pagination: keeps fetching pages until *max_results* is reached
    or no more pages remain.

    When *threads* is True, searches threads instead of individual messages
    and batches the ``threads().get()`` calls.
    """
    svc = service()
    if threads:
        return _search_threads(svc, query, max_results)
    return _search_messages(svc, query, max_results)


def _search_messages(svc, query: str, max_results: int) -> str:
    """Paginate messages().list() then batch messages().get()."""
    # --- collect stubs with pagination ---
    all_stubs: list[dict] = []
    page_token = None
    while len(all_stubs) < max_results:
        kwargs: dict = {
            "userId": "me",
            "q": query,
            "maxResults": min(100, max_results - len(all_stubs)),
        }
        if page_token:
            kwargs["pageToken"] = page_token
        result = svc.users().messages().list(**kwargs).execute()
        msgs = result.get("messages", [])
        all_stubs.extend(msgs)
        page_token = result.get("nextPageToken")
        if not page_token or not msgs:
            break

    all_stubs = all_stubs[:max_results]
    if not all_stubs:
        return "No messages found."

    # --- batch fetch in chunks of 100 ---
    collected: list[tuple[int, str]] = []

    errors: list[str] = []

    def _callback(request_id: str, response: dict, exception: Exception | None) -> None:
        if exception is not None:
            errors.append(f"batch fetch {request_id}: {exception}")
            return
        collected.append((int(request_id), _format_message(response)))

    for offset in range(0, len(all_stubs), 100):
        batch = svc.new_batch_http_request(callback=_callback)
        for j, stub in enumerate(all_stubs[offset : offset + 100]):
            req = svc.users().messages().get(userId="me", id=stub["id"], format="metadata")
            batch.add(req, request_id=str(offset + j))
        batch.execute()

    if errors:
        import logging

        logging.getLogger(__name__).warning(
            "gmail batch: %d/%d failed: %s", len(errors), len(all_stubs), errors[0]
        )

    collected.sort(key=lambda pair: pair[0])
    return "\n".join(line for _, line in collected)


def _search_threads(svc, query: str, max_results: int) -> str:
    """Paginate threads().list() then batch threads().get()."""
    # --- collect thread stubs with pagination ---
    all_stubs: list[dict] = []
    page_token = None
    while len(all_stubs) < max_results:
        kwargs: dict = {
            "userId": "me",
            "q": query,
            "maxResults": min(100, max_results - len(all_stubs)),
        }
        if page_token:
            kwargs["pageToken"] = page_token
        result = svc.users().threads().list(**kwargs).execute()
        threads = result.get("threads", [])
        all_stubs.extend(threads)
        page_token = result.get("nextPageToken")
        if not page_token or not threads:
            break

    all_stubs = all_stubs[:max_results]
    if not all_stubs:
        return "No messages found."

    # --- batch fetch in chunks of 100 ---
    collected: list[tuple[int, str]] = []

    errors: list[str] = []

    def _callback(request_id: str, response: dict, exception: Exception | None) -> None:
        if exception is not None:
            errors.append(f"batch fetch {request_id}: {exception}")
            return
        msgs = response.get("messages", [])
        thread_lines = [_format_message(m) for m in msgs]
        collected.append((int(request_id), "\n".join(thread_lines)))

    for offset in range(0, len(all_stubs), 100):
        batch = svc.new_batch_http_request(callback=_callback)
        for j, stub in enumerate(all_stubs[offset : offset + 100]):
            req = svc.users().threads().get(userId="me", id=stub["id"], format="metadata")
            batch.add(req, request_id=str(offset + j))
        batch.execute()

    if errors:
        import logging

        logging.getLogger(__name__).warning(
            "gmail thread batch: %d/%d failed: %s", len(errors), len(all_stubs), errors[0]
        )

    collected.sort(key=lambda pair: pair[0])
    return "\n\n".join(block for _, block in collected)


def resolve_thread_id(identifier: str) -> str:
    """Resolve a message ID or thread ID to the canonical thread ID.

    Gmail message IDs and thread IDs share the same format. For the first
    message in a thread they are identical; for replies they differ. This
    function accepts either and returns the thread ID by fetching the
    identifier as a message and reading its ``threadId`` field.
    """
    svc = service()
    msg = svc.users().messages().get(userId="me", id=identifier, format="minimal").execute()
    return msg.get("threadId", identifier)


def get_thread(thread_id: str) -> str:
    """Get full thread content.

    Accepts a thread ID **or** a message ID. If a message ID is passed,
    it is resolved to the owning thread ID first (one extra lightweight
    API call with ``format=minimal``).
    """
    from googleapiclient.errors import HttpError

    svc = service()
    try:
        thread = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
    except HttpError as exc:
        if exc.resp.status == 404:
            # Likely a message ID — resolve to the owning thread ID.
            resolved = resolve_thread_id(thread_id)
            thread = svc.users().threads().get(userId="me", id=resolved, format="full").execute()
        else:
            raise
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
            userId="me", id=msg_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()
    return f"Archived {len(message_ids)} message(s)."


def mark_read(message_ids: list[str]) -> str:
    """Mark messages as read (remove UNREAD label)."""
    svc = service()
    for msg_id in message_ids:
        svc.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
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
        for file_path in attachments:
            path = Path(file_path)
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type is None:
                mime_type = "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)
            with open(path, "rb") as f:
                file_data = f.read()
            part = MIMEBase(maintype, subtype)
            part.set_payload(file_data)
            encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=path.name)
            msg_mime.attach(part)

    msg_mime["to"] = to
    msg_mime["subject"] = subject
    if cc:
        msg_mime["cc"] = cc

    raw = base64.urlsafe_b64encode(msg_mime.as_bytes()).decode()
    send_body: dict = {"raw": raw}

    if reply_to_message_id:
        original = (
            svc.users()
            .messages()
            .get(userId="me", id=reply_to_message_id, format="metadata")
            .execute()
        )
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
    result = (
        svc.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
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
        action["removeLabelIds"] = [*action.get("removeLabelIds", []), "INBOX"]
    if mark_read:
        action["removeLabelIds"] = [*action.get("removeLabelIds", []), "UNREAD"]

    result = (
        svc.users()
        .settings()
        .filters()
        .create(
            userId="me",
            body={"criteria": criteria, "action": action},
        )
        .execute()
    )
    return f"Filter created: {result.get('id', 'unknown')}"
