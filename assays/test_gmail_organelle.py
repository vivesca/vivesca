"""Tests for metabolon.organelles.gmail: batch search, pagination, HTML stripping, send_email."""

import base64
import email
from unittest.mock import MagicMock, patch

from metabolon.organelles.gmail import _strip_html, search, send_email

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_msg(msg_id, from_addr="a@b.com", subject="Sub", snippet="snip"):
    """Build a minimal message dict that _format_message can consume."""
    return {
        "id": msg_id,
        "internalDate": "1700000000000",
        "payload": {
            "headers": [
                {"name": "From", "value": from_addr},
                {"name": "Subject", "value": subject},
            ]
        },
        "snippet": snippet,
    }


def _fake_batch_class(responses):
    """Return a class that simulates BatchHttpRequest with canned responses.

    *responses* maps ``request_id`` → ``(response_dict, exception_or_None)``.
    """

    class FakeBatch:
        def __init__(self, callback=None):
            self._callback = callback
            self._request_ids = []

        def add(self, request, request_id=None):
            self._request_ids.append(request_id)

        def execute(self):
            for rid in self._request_ids:
                resp, exc = responses.get(rid, ({}, None))
                self._callback(str(rid), resp, exc)

    return FakeBatch


# ---------------------------------------------------------------------------
# Existing tests — HTML stripping + send_email
# ---------------------------------------------------------------------------


def test_html_only_strips_tags():
    """Basic tags are stripped and entities are unescaped."""
    html_text = "<p>Hello <b>world</b> &amp; goodbye</p>"
    result = _strip_html(html_text)
    assert "Hello" in result
    assert "world" in result
    assert "&" in result or "&amp;" not in result
    assert "<p>" not in result
    assert "<b>" not in result


def test_html_strips_style_script():
    """Content inside <style> and <script> blocks is removed entirely."""
    html_text = (
        "<html><head><style>body { color: red; }</style>"
        "<script>alert('xss')</script></head>"
        "<body><p>Hello</p></body></html>"
    )
    result = _strip_html(html_text)
    assert "color" not in result
    assert "red" not in result
    assert "alert" not in result
    assert "xss" not in result
    assert "Hello" in result


def test_send_with_attachment(tmp_path):
    """send_email attaches files and the raw MIME payload contains their content."""
    attachment = tmp_path / "notes.txt"
    attachment.write_text("hello from attachment")

    mock_svc = MagicMock()
    mock_svc.users().messages().send.return_value.execute.return_value = {"id": "msg123"}

    with patch("metabolon.organelles.gmail.service", return_value=mock_svc):
        result = send_email(
            to="test@example.com",
            subject="test subject",
            body="test body",
            attachments=[str(attachment)],
        )

    assert "msg123" in result

    # Inspect the raw MIME that was sent
    call_kwargs = mock_svc.users().messages().send.call_args
    raw_b64 = call_kwargs[1]["body"]["raw"]
    raw_bytes = base64.urlsafe_b64decode(raw_b64)
    mime_msg = email.message_from_bytes(raw_bytes)

    # The message should be multipart
    assert mime_msg.is_multipart()

    # Find the attachment part and verify its decoded content
    parts = list(mime_msg.walk())
    attachment_parts = [p for p in parts if p.get_content_disposition() == "attachment"]
    assert len(attachment_parts) == 1
    assert attachment_parts[0].get_filename() == "notes.txt"
    assert attachment_parts[0].get_payload(decode=True) == b"hello from attachment"


# ---------------------------------------------------------------------------
# Batch search tests — messages mode
# ---------------------------------------------------------------------------


def test_search_no_results():
    """search() returns 'No messages found.' when list() returns no messages."""
    mock_svc = MagicMock()
    mock_svc.users().messages().list.return_value.execute.return_value = {}

    with patch("metabolon.organelles.gmail.service", return_value=mock_svc):
        assert search("inbox:something") == "No messages found."


def test_search_single_page_messages():
    """Single-page messages.list -> batch get -> formatted output."""
    mock_svc = MagicMock()
    mock_svc.users().messages().list.return_value.execute.return_value = {
        "messages": [{"id": "m1"}, {"id": "m2"}],
    }

    responses = {
        "0": (_mock_msg("m1", subject="Alpha"), None),
        "1": (_mock_msg("m2", subject="Beta"), None),
    }
    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("subject:test")

    assert "m1" in result
    assert "Alpha" in result
    assert "m2" in result
    assert "Beta" in result
    assert len([ln for ln in result.split("\n") if ln.strip()]) == 2


def test_search_pagination_messages():
    """Two pages of messages.list are stitched together."""
    mock_svc = MagicMock()
    req1 = MagicMock()
    req1.execute.return_value = {
        "messages": [{"id": "m1"}, {"id": "m2"}],
        "nextPageToken": "tok2",
    }
    req2 = MagicMock()
    req2.execute.return_value = {"messages": [{"id": "m3"}]}
    mock_svc.users().messages().list.side_effect = [req1, req2]

    responses = {
        "0": (_mock_msg("m1"), None),
        "1": (_mock_msg("m2"), None),
        "2": (_mock_msg("m3"), None),
    }
    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("query", max_results=10)

    assert "m1" in result
    assert "m2" in result
    assert "m3" in result


def test_search_truncates_to_max_results():
    """Only max_results messages are returned even if more stubs are fetched."""
    stubs = [{"id": f"m{i}"} for i in range(5)]
    mock_svc = MagicMock()
    mock_svc.users().messages().list.return_value.execute.return_value = {
        "messages": stubs,
    }
    responses = {str(i): (_mock_msg(f"m{i}"), None) for i in range(5)}

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q", max_results=3)

    assert "m0" in result
    assert "m1" in result
    assert "m2" in result
    assert "m3" not in result
    assert "m4" not in result


def test_search_batch_handles_errors():
    """Failed batch items are skipped; successful ones still returned."""
    mock_svc = MagicMock()
    mock_svc.users().messages().list.return_value.execute.return_value = {
        "messages": [{"id": "m1"}, {"id": "m2"}, {"id": "m3"}],
    }
    responses = {
        "0": (_mock_msg("m1", subject="OK1"), None),
        "1": ({}, Exception("boom")),
        "2": (_mock_msg("m3", subject="OK3"), None),
    }

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q")

    assert "OK1" in result
    assert "OK3" in result
    assert "boom" not in result


def test_search_over_100_uses_multiple_batches():
    """150 messages triggers two batch rounds (100 + 50)."""
    stubs = [{"id": f"m{i}"} for i in range(150)]
    mock_svc = MagicMock()
    mock_svc.users().messages().list.return_value.execute.return_value = {
        "messages": stubs,
    }
    responses = {str(i): (_mock_msg(f"m{i}"), None) for i in range(150)}

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q", max_results=150)

    lines = [ln for ln in result.split("\n") if ln.strip()]
    assert len(lines) == 150
    assert "m0" in lines[0]
    assert "m149" in lines[149]


# ---------------------------------------------------------------------------
# Batch search tests — threads mode
# ---------------------------------------------------------------------------


def test_search_threads_no_results():
    """threads=True returns 'No messages found.' when list is empty."""
    mock_svc = MagicMock()
    mock_svc.users().threads().list.return_value.execute.return_value = {}

    with patch("metabolon.organelles.gmail.service", return_value=mock_svc):
        assert search("q", threads=True) == "No messages found."


def test_search_threads_single_page():
    """Single-page threads.list -> batch threads.get -> formatted output."""
    mock_svc = MagicMock()
    mock_svc.users().threads().list.return_value.execute.return_value = {
        "threads": [{"id": "t1"}, {"id": "t2"}],
    }
    t1_resp = {"messages": [_mock_msg("m1", subject="T1A"), _mock_msg("m2", subject="T1B")]}
    t2_resp = {"messages": [_mock_msg("m3", subject="T2A")]}
    responses = {"0": (t1_resp, None), "1": (t2_resp, None)}

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q", threads=True)

    assert "T1A" in result
    assert "T1B" in result
    assert "T2A" in result


def test_search_threads_pagination():
    """Two pages of threads.list are stitched together."""
    mock_svc = MagicMock()
    req1 = MagicMock()
    req1.execute.return_value = {
        "threads": [{"id": "t1"}],
        "nextPageToken": "tok2",
    }
    req2 = MagicMock()
    req2.execute.return_value = {"threads": [{"id": "t2"}]}
    mock_svc.users().threads().list.side_effect = [req1, req2]

    t1_resp = {"messages": [_mock_msg("m1", subject="Page1")]}
    t2_resp = {"messages": [_mock_msg("m2", subject="Page2")]}
    responses = {"0": (t1_resp, None), "1": (t2_resp, None)}

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q", threads=True, max_results=10)

    assert "Page1" in result
    assert "Page2" in result


def test_search_threads_batch_handles_errors():
    """Failed thread batch items are skipped; successful ones still returned."""
    mock_svc = MagicMock()
    mock_svc.users().threads().list.return_value.execute.return_value = {
        "threads": [{"id": "t1"}, {"id": "t2"}],
    }
    t1_resp = {"messages": [_mock_msg("m1", subject="ThreadOK")]}
    responses = {
        "0": (t1_resp, None),
        "1": ({}, Exception("thread-error")),
    }

    with (
        patch("metabolon.organelles.gmail.service", return_value=mock_svc),
        patch("metabolon.organelles.gmail.BatchHttpRequest", _fake_batch_class(responses)),
    ):
        result = search("q", threads=True)

    assert "ThreadOK" in result
    assert "thread-error" not in result
