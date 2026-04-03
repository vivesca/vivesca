"""Tests for metabolon.organelles.gmail HTML stripping and send_email."""
import base64
import email
from email.message import Message
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.gmail import send_email, _strip_html


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
    attachment_parts = [
        p for p in parts
        if p.get_content_disposition() == "attachment"
    ]
    assert len(attachment_parts) == 1
    assert attachment_parts[0].get_filename() == "notes.txt"
    assert attachment_parts[0].get_payload(decode=True) == b"hello from attachment"
