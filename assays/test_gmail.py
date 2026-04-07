"""Smoke tests for metabolon.organelles.gmail.

Mocks the Google API service object to verify:
  - search (messages + threads)
  - get_thread / get_message
  - archive / mark_read
  - batch operations use svc.new_batch_http_request(), not BatchHttpRequest()
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_msg(
    msg_id: str = "m1",
    thread_id: str = "t1",
    subject: str = "Test",
    sender: str = "alice@example.com",
    snippet: str = "hello",
    body_data: str = "",
    internal_date: str = "1700000000000",
) -> dict:
    """Build a minimal Gmail message resource dict."""
    payload: dict = {
        "headers": [
            {"name": "From", "value": sender},
            {"name": "Subject", "value": subject},
        ],
    }
    if body_data:
        import base64

        payload["body"] = {"data": base64.urlsafe_b64encode(body_data.encode()).decode()}
        payload["mimeType"] = "text/plain"

    return {
        "id": msg_id,
        "threadId": thread_id,
        "snippet": snippet,
        "internalDate": internal_date,
        "payload": payload,
    }


class _FakeRequest:
    """Fake API request object returned by the fluent builder chain."""

    def __init__(self, result: dict | None = None, side_effect=None):
        self._result = result
        self._side_effect = side_effect

    def execute(self):
        if self._side_effect:
            return self._side_effect()
        return self._result


class _FakeBatch:
    """Fake batch request that records added requests and executes callbacks immediately."""

    def __init__(self, callback=None):
        self._callback = callback
        self._requests: list[tuple] = []

    def add(self, request, request_id=None):
        self._requests.append((request, request_id))

    def execute(self):
        for request, request_id in self._requests:
            if self._callback:
                try:
                    response = request.execute()
                    self._callback(request_id, response, None)
                except Exception as exc:
                    self._callback(request_id, None, exc)


def _make_svc(
    list_result: dict | None = None,
    get_result: dict | None = None,
    thread_get_result: dict | None = None,
    batch_cls=None,
) -> MagicMock:
    """Build a mock service with the fluent Gmail API chain."""
    svc = MagicMock()

    # svc.new_batch_http_request(callback=...) -> _FakeBatch(callback)
    if batch_cls is None:
        batch_cls = _FakeBatch
    svc.new_batch_http_request = MagicMock(side_effect=lambda callback=None: batch_cls(callback))

    # messages().list().execute()
    msg_mock = MagicMock()
    msg_list_req = _FakeRequest(result=list_result or {})
    msg_mock.list.return_value = msg_list_req

    # messages().get().execute()
    msg_get_req = _FakeRequest(result=get_result or _make_msg())
    msg_mock.get.return_value = msg_get_req

    # messages().modify().execute()
    msg_modify_req = _FakeRequest(result={})
    msg_mock.modify.return_value = msg_modify_req

    svc.users.return_value.messages.return_value = msg_mock

    # threads().list().execute()
    thread_mock = MagicMock()
    thread_list_req = _FakeRequest(result=list_result or {})
    thread_mock.list.return_value = thread_list_req

    # threads().get().execute()
    thread_get_req = _FakeRequest(result=thread_get_result or {"id": "t1", "messages": [_make_msg()]})
    thread_mock.get.return_value = thread_get_req

    svc.users.return_value.threads.return_value = thread_mock

    return svc


# ---------------------------------------------------------------------------
# Tests: search (messages)
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_search_messages_returns_formatted(mock_service):
    svc = _make_svc(
        list_result={"messages": [{"id": "m1", "threadId": "t1"}]},
        get_result=_make_msg(msg_id="m1", subject="Hello"),
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import search

    result = search("in:inbox", max_results=5)
    assert "m1" in result
    assert "Hello" in result


@patch("metabolon.organelles.gmail.service")
def test_search_messages_empty(mock_service):
    svc = _make_svc(list_result={})
    mock_service.return_value = svc

    from metabolon.organelles.gmail import search

    result = search("nonexistent:query")
    assert result == "No messages found."


# ---------------------------------------------------------------------------
# Tests: search (threads)
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_search_threads_returns_formatted(mock_service):
    svc = _make_svc(
        list_result={"threads": [{"id": "t1"}]},
        thread_get_result={"id": "t1", "messages": [_make_msg(msg_id="m1", subject="Thread sub")]},
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import search

    result = search("in:inbox", threads=True)
    assert "Thread sub" in result


# ---------------------------------------------------------------------------
# Tests: get_thread
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_get_thread_returns_messages(mock_service):
    svc = _make_svc(
        thread_get_result={
            "id": "t1",
            "messages": [
                _make_msg(msg_id="m1", subject="First"),
                _make_msg(msg_id="m2", subject="Re: First"),
            ],
        }
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import get_thread

    result = get_thread("t1")
    assert "First" in result
    assert "Re: First" in result


# ---------------------------------------------------------------------------
# Tests: get_message
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_get_message_full(mock_service):
    svc = _make_svc(
        get_result=_make_msg(msg_id="m42", subject="Single", body_data="body text"),
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import get_message

    result = get_message("m42", full=True)
    assert "m42" in result
    assert "Single" in result
    assert "body text" in result


@patch("metabolon.organelles.gmail.service")
def test_get_message_metadata(mock_service):
    svc = _make_svc(
        get_result=_make_msg(msg_id="m99", subject="Meta only"),
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import get_message

    result = get_message("m99", full=False)
    assert "m99" in result
    assert "Meta only" in result


# ---------------------------------------------------------------------------
# Tests: archive
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_archive_removes_inbox_label(mock_service):
    svc = _make_svc()
    mock_service.return_value = svc

    from metabolon.organelles.gmail import archive

    result = archive(["m1", "m2"])
    assert "Archived 2 message(s)" in result
    modify_mock = svc.users.return_value.messages.return_value.modify
    assert modify_mock.call_count == 2
    modify_mock.assert_any_call(
        userId="me", id="m1", body={"removeLabelIds": ["INBOX"]}
    )
    modify_mock.assert_any_call(
        userId="me", id="m2", body={"removeLabelIds": ["INBOX"]}
    )


# ---------------------------------------------------------------------------
# Tests: mark_read
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
def test_mark_read_removes_unread_label(mock_service):
    svc = _make_svc()
    mock_service.return_value = svc

    from metabolon.organelles.gmail import mark_read

    result = mark_read(["m10"])
    assert "Marked 1 message(s) as read" in result
    modify_mock = svc.users.return_value.messages.return_value.modify
    modify_mock.assert_called_once_with(
        userId="me", id="m10", body={"removeLabelIds": ["UNREAD"]}
    )


# ---------------------------------------------------------------------------
# Tests: batch uses svc.new_batch_http_request, not BatchHttpRequest
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.gmail.service")
@patch("metabolon.organelles.gmail.BatchHttpRequest")
def test_search_uses_new_batch_not_batchhttprequest(mock_batch_cls, mock_service):
    """Verify search builds batches via svc.new_batch_http_request(),
    not by directly instantiating BatchHttpRequest."""
    svc = _make_svc(
        list_result={"messages": [{"id": "m1", "threadId": "t1"}]},
        get_result=_make_msg(msg_id="m1"),
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import search

    search("in:inbox")
    # svc.new_batch_http_request must have been called
    assert svc.new_batch_http_request.called, "Expected svc.new_batch_http_request() to be called"
    # BatchHttpRequest constructor must NOT have been called
    mock_batch_cls.assert_not_called()


@patch("metabolon.organelles.gmail.service")
def test_search_batch_callback_logs_errors(mock_service):
    """Batch callbacks must log errors, not silently discard them.

    The gmail module imports `logging` inside the function body (not at
    module level), so we patch the stdlib `logging` module directly and
    verify the warning is emitted.
    """
    import logging

    class _ErrorBatch:
        """Batch that simulates a failure in one request."""
        def __init__(self, callback=None):
            self._callback = callback

        def add(self, request, request_id=None):
            pass

        def execute(self):
            if self._callback:
                self._callback("0", None, RuntimeError("API error"))

    svc = _make_svc(
        list_result={"messages": [{"id": "m1", "threadId": "t1"}]},
        get_result=_make_msg(msg_id="m1"),
        batch_cls=_ErrorBatch,
    )
    mock_service.return_value = svc

    from metabolon.organelles.gmail import search

    with patch.object(logging, "getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        result = search("test")

    # Verify the warning was logged with batch failure info.
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args
    assert "batch" in call_args[0][0].lower() or "failed" in call_args[0][0].lower()
