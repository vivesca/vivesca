from __future__ import annotations

"""Tests for gog — Gmail CLI effector.

Uses exec-based loading (no import) and subprocess for CLI integration.
API calls are mocked to avoid real Gmail auth.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

GOG = Path.home() / "germline" / "effectors" / "gog"


def _run(*args: str, stdin_data: str | None = None) -> subprocess.CompletedProcess:
    """Run gog as a subprocess."""
    cmd = [sys.executable, str(GOG), *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15)


def _load_gog():
    """Load gog module by exec-ing its source (skip shebang)."""
    source = open(str(GOG)).read()
    ns: dict = {"__name__": "gog_test", "__doc__": None}
    exec(source, ns)
    return ns


_mod = _load_gog()
build_parser = _mod["build_parser"]
_format_row = _mod["_format_row"]
_header = _mod["_header"]
_decode_body = _mod["_decode_body"]


# ── CLI help / parsing ───────────────────────────────────────────────


class TestCLIParsing:
    """Test argument parsing without Gmail auth."""

    def test_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "gog" in r.stdout.lower()

    def test_gmail_help(self):
        r = _run("gmail", "--help")
        assert r.returncode == 0

    def test_gmail_read_help(self):
        r = _run("gmail", "read", "--help")
        assert r.returncode == 0
        assert "--full" in r.stdout
        assert "--unread" in r.stdout
        assert "--from" in r.stdout
        assert "--after" in r.stdout

    def test_gmail_send_help(self):
        r = _run("gmail", "send", "--help")
        assert r.returncode == 0
        assert "--to" in r.stdout
        assert "--subject" in r.stdout
        assert "--body" in r.stdout

    def test_gmail_reply_help(self):
        r = _run("gmail", "reply", "--help")
        assert r.returncode == 0
        assert "--id" in r.stdout
        assert "--body" in r.stdout

    def test_gmail_archive_help(self):
        r = _run("gmail", "archive", "--help")
        assert r.returncode == 0
        assert "--id" in r.stdout

    def test_gmail_search_help(self):
        r = _run("gmail", "search", "--help")
        assert r.returncode == 0
        assert "query" in r.stdout

    def test_no_command_shows_help(self):
        r = _run()
        assert r.returncode == 0
        assert "gog" in r.stdout.lower()

    def test_search_requires_query(self):
        r = _run("gmail", "search")
        assert r.returncode != 0

    def test_send_requires_params(self):
        r = _run("gmail", "send")
        assert r.returncode != 0


# ── Parser structure ─────────────────────────────────────────────────


class TestParser:
    """Verify parser returns correct namespace."""

    def test_read_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["gmail", "read"])
        assert args.command == "gmail"
        assert args.gmail_command == "read"
        assert args.full is False
        assert args.unread is False
        assert args.from_ is None
        assert args.after is None
        assert args.max == 20

    def test_read_all_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "gmail", "read", "--full", "--unread",
            "--from", "alice@example.com",
            "--after", "2025/01/01",
            "--max", "50",
        ])
        assert args.full is True
        assert args.unread is True
        assert args.from_ == "alice@example.com"
        assert args.after == "2025/01/01"
        assert args.max == 50

    def test_send_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "gmail", "send",
            "--to", "bob@example.com",
            "--subject", "Hello",
            "--body", "World",
        ])
        assert args.to == "bob@example.com"
        assert args.subject == "Hello"
        assert args.body == "World"

    def test_reply_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "gmail", "reply", "--id", "msg123", "--body", "reply text",
        ])
        assert args.id == "msg123"
        assert args.body == "reply text"

    def test_archive_flags(self):
        parser = build_parser()
        args = parser.parse_args(["gmail", "archive", "--id", "msg456"])
        assert args.id == "msg456"

    def test_search_flags(self):
        parser = build_parser()
        args = parser.parse_args(["gmail", "search", "is:unread", "--max", "10"])
        assert args.query == "is:unread"
        assert args.max == 10

    def test_search_limit_alias(self):
        parser = build_parser()
        args = parser.parse_args(["gmail", "search", "test", "--limit", "5"])
        assert args.limit == 5

    def test_batch_modify_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "gmail", "batch", "modify", "id1", "id2",
            "--remove", "UNREAD", "--remove", "INBOX",
        ])
        assert args.ids == ["id1", "id2"]
        assert args.remove == ["UNREAD", "INBOX"]


# ── Helper functions ─────────────────────────────────────────────────


class TestHelpers:
    """Test internal formatting helpers."""

    def test_format_row(self):
        msg = {
            "id": "abc",
            "internalDate": "1700000000000",
            "snippet": "Hello world preview",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Alice <alice@example.com>"},
                    {"name": "Subject", "value": "Test Subject"},
                ]
            },
        }
        row = _format_row(msg)
        assert "Alice <alice@example.com>" in row
        assert "Test Subject" in row
        assert "Hello world preview" in row
        assert " | " in row

    def test_header_extraction(self):
        msg = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "bob@test.com"},
                    {"name": "Subject", "value": "Hi"},
                ]
            }
        }
        assert _header(msg, "From") == "bob@test.com"
        assert _header(msg, "Subject") == "Hi"
        assert _header(msg, "Cc") == ""

    def test_decode_body_plain(self):
        import base64
        payload = {"body": {"data": base64.urlsafe_b64encode(b"Hello body").decode()}}
        assert _decode_body(payload) == "Hello body"

    def test_decode_body_multipart(self):
        import base64
        text_part = {
            "mimeType": "text/plain",
            "body": {"data": base64.urlsafe_b64encode(b"Plain part").decode()},
        }
        payload = {"body": {}, "parts": [text_part]}
        assert _decode_body(payload) == "Plain part"

    def test_decode_body_empty(self):
        assert _decode_body({}) == ""


# ── Functional tests (mocked API) ────────────────────────────────────

from io import StringIO

import pytest


def _mock_msg(
    msg_id: str = "m1",
    from_addr: str = "alice@example.com",
    subject: str = "Test",
    snippet: str = "A test message",
    date_ms: str = "1700000000000",
) -> dict:
    return {
        "id": msg_id,
        "threadId": "t1",
        "labelIds": ["INBOX", "UNREAD"],
        "internalDate": date_ms,
        "snippet": snippet,
        "payload": {
            "headers": [
                {"name": "From", "value": from_addr},
                {"name": "Subject", "value": subject},
                {"name": "To", "value": "me@example.com"},
                {"name": "Message-ID", "value": f"<{msg_id}@mail>"},
                {"name": "References", "value": ""},
            ],
            "body": {"data": ""},
        },
    }


@pytest.fixture
def mock_service():
    """Monkey-patch _mod['_service'] to return a configured MagicMock."""
    svc = MagicMock()
    original = _mod["_service"]
    _mod["_service"] = lambda: svc
    yield svc
    _mod["_service"] = original


class TestCmdRead:
    """Test cmd_read with mocked Gmail service."""

    def test_read_inbox(self, mock_service):
        svc = mock_service
        svc.users().messages().list().execute.return_value = {
            "messages": [{"id": "m1"}]
        }
        svc.users().messages().get().execute.return_value = _mock_msg()

        args = argparse.Namespace(
            query=None, max=20, unread=False, from_=None, after=None, full=False
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_read"](args)
        output = out.getvalue()
        assert "m1" in output
        assert "alice@example.com" in output
        assert "Test" in output
        assert "A test message" in output

    def test_read_empty(self, mock_service):
        svc = mock_service
        svc.users().messages().list().execute.return_value = {}

        args = argparse.Namespace(
            query=None, max=20, unread=False, from_=None, after=None, full=False
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_read"](args)
        assert "No messages" in out.getvalue()


class TestCmdSend:
    """Test cmd_send with mocked Gmail service."""

    def test_send(self, mock_service):
        svc = mock_service
        svc.users().messages().send().execute.return_value = {"id": "sent1"}

        args = argparse.Namespace(
            to="bob@test.com", subject="Hi", body="Hello",
            reply_to_message_id=None, quote=False
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_send"](args)
        assert "Sent: sent1" in out.getvalue()
        svc.users().messages().send.assert_called()

    def test_send_reply_threads(self, mock_service):
        svc = mock_service
        svc.users().messages().get().execute.return_value = _mock_msg("orig1")
        svc.users().messages().send().execute.return_value = {"id": "sent2"}

        args = argparse.Namespace(
            to="bob@test.com", subject="Re: Test",
            body="Reply body",
            reply_to_message_id="orig1", quote=False
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_send"](args)
        assert "Sent: sent2" in out.getvalue()


class TestCmdReply:
    """Test cmd_reply with mocked Gmail service."""

    def test_reply(self, mock_service):
        svc = mock_service
        svc.users().messages().get().execute.return_value = _mock_msg("orig1")
        svc.users().messages().send().execute.return_value = {"id": "rep1"}

        args = argparse.Namespace(id="orig1", body="Reply text")
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_reply"](args)
        assert "Replied: rep1" in out.getvalue()
        call_body = svc.users().messages().send.call_args[1]["body"]
        assert call_body["threadId"] == "t1"


class TestCmdArchive:
    """Test cmd_archive with mocked Gmail service."""

    def test_archive(self, mock_service):
        svc = mock_service
        svc.users().messages().modify().execute.return_value = {}

        args = argparse.Namespace(id="m1")
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_archive"](args)
        assert "Archived: m1" in out.getvalue()
        # Called once with keyword args, once as chained .execute()
        calls = svc.users().messages().modify.call_args_list
        assert any(c == ((userId="me",), {"id": "m1", "body": {"removeLabelIds": ["INBOX"]}}) for c in calls)


class TestCmdSearch:
    """Test cmd_search with mocked Gmail service."""

    def test_search(self, mock_service):
        svc = mock_service
        svc.users().messages().list().execute.return_value = {
            "messages": [{"id": "s1"}]
        }
        svc.users().messages().get().execute.return_value = _mock_msg("s1")

        args = argparse.Namespace(query="from:alice", max=20, limit=None)
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_search"](args)
        assert "s1" in out.getvalue()

    def test_search_empty(self, mock_service):
        svc = mock_service
        svc.users().messages().list().execute.return_value = {}

        args = argparse.Namespace(query="nonexistent", max=20, limit=None)
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_search"](args)
        assert "No messages" in out.getvalue()


class TestCmdBatchModify:
    """Test batch modify with mocked Gmail service."""

    def test_batch_modify(self, mock_service):
        svc = mock_service
        svc.users().messages().batchModify().execute.return_value = {}

        args = argparse.Namespace(
            ids=["m1", "m2"], add=None, remove=["UNREAD", "INBOX"]
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_batch_modify"](args)
        assert "Modified 2 messages" in out.getvalue()


class TestCmdDrafts:
    """Test draft operations with mocked Gmail service."""

    def test_drafts_list_empty(self, mock_service):
        svc = mock_service
        svc.users().drafts().list().execute.return_value = {}

        args = argparse.Namespace(max=20, plain=False)
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_drafts_list"](args)
        assert "No drafts" in out.getvalue()

    def test_drafts_create(self, mock_service):
        svc = mock_service
        svc.users().drafts().create().execute.return_value = {"id": "d1"}

        args = argparse.Namespace(
            to="bob@test.com", cc=None, subject="Draft",
            body="Draft body", reply_to_message_id=None, attach=None
        )
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_drafts_create"](args)
        assert "Draft created: d1" in out.getvalue()

    def test_drafts_delete(self, mock_service):
        svc = mock_service
        svc.users().drafts().delete().execute.return_value = {}

        args = argparse.Namespace(id="d1", force=True)
        with patch("sys.stdout", new_callable=StringIO) as out:
            _mod["cmd_drafts_delete"](args)
        assert "Draft deleted: d1" in out.getvalue()
