"""Tests for metabolon/enzymes/endosomal.py - Gmail MCP tool wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from metabolon.morphology.base import EffectorResult


# ── Load the module and patch dependencies ───────────────────────────────


@pytest.fixture
def mock_invoke_organelle():
    """Mock invoke_organelle to avoid actual CLI calls."""
    with patch("metabolon.enzymes.endosomal.invoke_organelle") as mock:
        mock.return_value = "Mock output"
        yield mock


@pytest.fixture
def mock_synthesize():
    """Mock synthesize to avoid actual LLM calls."""
    with patch("metabolon.enzymes.endosomal.synthesize") as mock:
        mock.return_value = "action_required"
        yield mock


@pytest.fixture
def endosomal():
    """Import and return the endosomal function with mocked dependencies."""
    from metabolon.enzymes.endosomal import endosomal
    return endosomal


# ── Action validation tests ──────────────────────────────────────────────


def test_endosomal_unknown_action(endosomal):
    """endosomal returns error for unknown action."""
    result = endosomal(action="unknown")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message


def test_endosomal_action_case_insensitive(endosomal, mock_invoke_organelle):
    """endosomal handles action case-insensitively."""
    result = endosomal(action="SEARCH", query="test")
    assert result.success is True or hasattr(result, "output")


# ── Search action tests ───────────────────────────────────────────────────


def test_endosomal_search_requires_query(endosomal):
    """endosomal search requires query parameter."""
    result = endosomal(action="search", query="")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "query" in result.message.lower()


def test_endosomal_search_success(endosomal, mock_invoke_organelle):
    """endosomal search invokes Gmail search."""
    result = endosomal(action="search", query="from:boss@company.com")
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert call_args[0][0] == "gog"
    assert "gmail" in call_args[0][1]
    assert "search" in call_args[0][1]
    assert hasattr(result, "output")


# ── Thread action tests ───────────────────────────────────────────────────


def test_endosomal_thread_requires_thread_id(endosomal):
    """endosomal thread requires thread_id parameter."""
    result = endosomal(action="thread", thread_id="")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "thread_id" in result.message.lower()


def test_endosomal_thread_success(endosomal, mock_invoke_organelle):
    """endosomal thread invokes Gmail thread get."""
    result = endosomal(action="thread", thread_id="12345")
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "thread" in call_args[0][1]
    assert "12345" in call_args[0][1]


# ── Categorize action tests ───────────────────────────────────────────────


def test_endosomal_categorize_requires_email_text(endosomal):
    """endosomal categorize requires email_text parameter."""
    result = endosomal(action="categorize", email_text="")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "email_text" in result.message.lower()


def test_endosomal_categorize_deterministic(endosomal):
    """endosomal categorize uses deterministic classification first."""
    # Email that should be classified as archive_now (automated sender)
    result = endosomal(
        action="categorize",
        email_text="From: noreply@github.com\nSubject: PR merged\n\nYour PR was merged."
    )
    
    assert hasattr(result, "output")
    assert "archive_now" in result.output


def test_endosomal_categorize_falls_back_to_symbiont(endosomal, mock_synthesize):
    """endosomal categorize falls back to LLM for ambiguous emails."""
    # Clear classification cache
    with patch("metabolon.organelles.endosomal.classify", return_value=""):
        result = endosomal(
            action="categorize",
            email_text="Subject: Hello\n\nJust saying hi."
        )
        
        # Should have called synthesize
        mock_synthesize.assert_called_once()


def test_endosomal_categorize_unclassified(endosomal, mock_synthesize):
    """endosomal categorize handles unclassified LLM output."""
    mock_synthesize.return_value = "unknown_category"
    
    with patch("metabolon.organelles.endosomal.classify", return_value=""):
        result = endosomal(
            action="categorize",
            email_text="Subject: Test\n\nBody"
        )
        
        assert hasattr(result, "output")
        assert "Unclassified" in result.output


# ── Archive action tests ──────────────────────────────────────────────────


def test_endosomal_archive_requires_message_ids(endosomal):
    """endosomal archive requires message_ids parameter."""
    result = endosomal(action="archive", message_ids=[])
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "message_ids" in result.message.lower()


def test_endosomal_archive_success(endosomal, mock_invoke_organelle):
    """endosomal archive invokes Gmail archive."""
    result = endosomal(action="archive", message_ids=["msg1", "msg2"])
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "archive" in call_args[0][1]
    assert "msg1" in call_args[0][1]
    assert "msg2" in call_args[0][1]
    assert result.success is True


# ── Mark read action tests ────────────────────────────────────────────────


def test_endosomal_mark_read_requires_message_ids(endosomal):
    """endosomal mark_read requires message_ids parameter."""
    result = endosomal(action="mark_read", message_ids=[])
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "message_ids" in result.message.lower()


def test_endosomal_mark_read_success(endosomal, mock_invoke_organelle):
    """endosomal mark_read invokes Gmail mark-read."""
    result = endosomal(action="mark_read", message_ids=["msg1"])
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "mark-read" in call_args[0][1]
    assert result.success is True


# ── Label action tests ────────────────────────────────────────────────────


def test_endosomal_label_requires_name(endosomal):
    """endosomal label requires name parameter."""
    result = endosomal(action="label", name="")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "name" in result.message.lower()


def test_endosomal_label_success(endosomal, mock_invoke_organelle):
    """endosomal label invokes Gmail labels create."""
    result = endosomal(action="label", name="Work")
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "labels" in call_args[0][1]
    assert "create" in call_args[0][1]
    assert "Work" in call_args[0][1]
    assert result.success is True


# ── Send action tests ─────────────────────────────────────────────────────


def test_endosomal_send_new_email_requires_params(endosomal):
    """endosomal send requires to, subject, body for new emails."""
    result = endosomal(action="send")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "to" in result.message.lower() or "subject" in result.message.lower()


def test_endosomal_send_new_email_success(endosomal, mock_invoke_organelle):
    """endosomal send invokes Gmail send for new emails."""
    result = endosomal(
        action="send",
        to="recipient@example.com",
        subject="Test Subject",
        body="Test body content"
    )
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "send" in call_args[0][1]
    assert "recipient@example.com" in call_args[0][1]
    assert result.success is True


def test_endosomal_send_reply(endosomal, mock_invoke_organelle):
    """endosomal send handles reply with reply_to_message_id."""
    result = endosomal(
        action="send",
        reply_to_message_id="msg123",
        body="Reply content"
    )
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "--reply-to-message-id" in call_args[0][1]
    assert "msg123" in call_args[0][1]
    assert result.success is True


def test_endosomal_send_with_cc(endosomal, mock_invoke_organelle):
    """endosomal send handles cc parameter."""
    result = endosomal(
        action="send",
        to="to@example.com",
        subject="Subject",
        body="Body",
        cc="cc@example.com"
    )
    
    call_args = mock_invoke_organelle.call_args
    assert "--cc" in call_args[0][1]


def test_endosomal_send_with_attachment(endosomal, mock_invoke_organelle):
    """endosomal send handles attach parameter."""
    result = endosomal(
        action="send",
        to="to@example.com",
        subject="Subject",
        body="Body",
        attach=["/path/to/file.pdf"]
    )
    
    call_args = mock_invoke_organelle.call_args
    assert "--attach" in call_args[0][1]


# ── Filter action tests ───────────────────────────────────────────────────


def test_endosomal_filter_requires_criteria(endosomal):
    """endosomal filter requires from_sender or subject_pattern."""
    result = endosomal(action="filter")
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "from_sender" in result.message.lower() or "subject_pattern" in result.message.lower()


def test_endosomal_filter_requires_action(endosomal):
    """endosomal filter requires at least one action (add_label, archive, mark_read)."""
    result = endosomal(
        action="filter",
        from_sender="spam@example.com"
    )
    
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "add_label" in result.message.lower() or "archive" in result.message.lower()


def test_endosomal_filter_success_dry_run(endosomal, mock_invoke_organelle):
    """endosomal filter creates filter in dry-run mode by default."""
    result = endosomal(
        action="filter",
        from_sender="newsletter@example.com",
        add_label="Newsletters",
        archive=True
    )
    
    mock_invoke_organelle.assert_called_once()
    call_args = mock_invoke_organelle.call_args
    assert "filters" in call_args[0][1]
    assert "create" in call_args[0][1]
    assert "--dry-run" in call_args[0][1]
    assert result.success is True
    assert "[DRY RUN]" in result.message


def test_endosomal_filter_not_dry_run(endosomal, mock_invoke_organelle):
    """endosomal filter can disable dry-run mode."""
    result = endosomal(
        action="filter",
        from_sender="newsletter@example.com",
        add_label="Newsletters",
        dry_run=False
    )
    
    call_args = mock_invoke_organelle.call_args
    assert "--dry-run" not in call_args[0][1]
    assert "[DRY RUN]" not in result.message


def test_endosomal_filter_subject_pattern(endosomal, mock_invoke_organelle):
    """endosomal filter handles subject_pattern parameter."""
    result = endosomal(
        action="filter",
        subject_pattern="[Newsletter]",
        mark_read=True
    )
    
    call_args = mock_invoke_organelle.call_args
    assert "--subject" in call_args[0][1]


def test_endosomal_filter_all_actions(endosomal, mock_invoke_organelle):
    """endosomal filter can combine add_label, archive, and mark_read."""
    result = endosomal(
        action="filter",
        from_sender="promo@example.com",
        add_label="Promotions",
        archive=True,
        mark_read=True
    )
    
    call_args = mock_invoke_organelle.call_args
    assert "--add-label" in call_args[0][1]
    assert "--archive" in call_args[0][1]
    assert "--mark-read" in call_args[0][1]


# ── Result type tests ─────────────────────────────────────────────────────


def test_endosomal_result_has_output_for_read_actions(endosomal, mock_invoke_organelle):
    """Read actions (search, thread, categorize) return EndosomalResult with output."""
    # Search
    result = endosomal(action="search", query="test")
    assert hasattr(result, "output")
    
    # Thread
    result = endosomal(action="thread", thread_id="123")
    assert hasattr(result, "output")
    
    # Categorize (deterministic case)
    result = endosomal(action="categorize", email_text="From: noreply@test.com\n\nBody")
    assert hasattr(result, "output")


def test_endosomal_result_is_effector_for_mutations(endosomal, mock_invoke_organelle):
    """Mutation actions return EffectorResult with success/message."""
    # Archive
    result = endosomal(action="archive", message_ids=["msg1"])
    assert isinstance(result, EffectorResult)
    assert hasattr(result, "success")
    assert hasattr(result, "message")
    
    # Label
    result = endosomal(action="label", name="Test")
    assert isinstance(result, EffectorResult)
    
    # Send
    result = endosomal(action="send", to="a@b.com", subject="S", body="B")
    assert isinstance(result, EffectorResult)
