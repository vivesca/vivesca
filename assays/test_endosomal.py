"""Tests for endosomal enzyme module."""

from unittest.mock import patch, ANY

from metabolon.enzymes.endosomal import endosomal, EndosomalResult, EffectorResult
from metabolon.organelles import endosomal as endosomal_organelle


def test_endosomal_unknown_action():
    """Test unknown action returns error message."""
    result = endosomal(action="invalid")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Unknown action" in result.message
    assert "Valid: search, thread, categorize, archive, mark_read, label, send, filter" in result.message


def test_endosomal_search_missing_query():
    """Test search without required query returns error."""
    result = endosomal(action="search")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "search requires: query" in result.message


def test_endosomal_thread_missing_thread_id():
    """Test thread without required thread_id returns error."""
    result = endosomal(action="thread")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "thread requires: thread_id" in result.message


def test_endosomal_categorize_missing_email_text():
    """Test categorize without required email_text returns error."""
    result = endosomal(action="categorize")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "categorize requires: email_text" in result.message


def test_endosomal_archive_missing_message_ids():
    """Test archive without required message_ids returns error."""
    result = endosomal(action="archive")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "archive requires: message_ids" in result.message

    result = endosomal(action="archive", message_ids=[])
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "archive requires: message_ids" in result.message


def test_endosomal_mark_read_missing_message_ids():
    """Test mark_read without required message_ids returns error."""
    result = endosomal(action="mark_read")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "mark_read requires: message_ids" in result.message

    result = endosomal(action="mark_read", message_ids=[])
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "mark_read requires: message_ids" in result.message


def test_endosomal_label_missing_name():
    """Test label without required name returns error."""
    result = endosomal(action="label")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "label requires: name" in result.message


def test_endosomal_send_missing_params():
    """Test send with missing required parameters returns error."""
    # New email missing to, subject, body
    result = endosomal(action="send", to="test@example.com")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "New emails require to, subject, and body" in result.message

    result = endosomal(action="send", to="test@example.com", subject="Test")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "New emails require to, subject, and body" in result.message


def test_endosomal_filter_missing_criteria():
    """Test filter without at least one criteria returns error."""
    result = endosomal(action="filter")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Provide at least one of: from_sender, subject_pattern" in result.message


def test_endosomal_filter_missing_action():
    """Test filter without at least one action returns error."""
    result = endosomal(action="filter", from_sender="test@example.com")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Provide at least one action: add_label, archive, or mark_read" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_search_success(mock_invoke):
    """Test search action calls invoke_organelle correctly."""
    mock_invoke.return_value = "Found 5 messages"

    result = endosomal(action="search", query="meeting")

    mock_invoke.assert_called_once_with("gog", ["gmail", "search", "meeting", "--plain"], timeout=30)
    assert isinstance(result, EndosomalResult)
    assert result.output == "Found 5 messages"


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_thread_success(mock_invoke):
    """Test thread action calls invoke_organelle correctly."""
    mock_invoke.return_value = "Full thread content here"

    result = endosomal(action="thread", thread_id="12345")

    mock_invoke.assert_called_once_with("gog", ["gmail", "thread", "get", "12345", "--full"], timeout=60)
    assert isinstance(result, EndosomalResult)
    assert result.output == "Full thread content here"


def test_endosomal_categorize_deterministic_hit():
    """Test categorize action uses deterministic classification when it matches."""
    # This should match sender_is_automated
    email_text = """From: noreply@github.com
Subject: Your latest push

Your push to main was successful.
"""

    with patch("metabolon.enzymes.endosomal.synthesize") as mock_synthesize:
        result = endosomal(action="categorize", email_text=email_text)

        mock_synthesize.assert_not_called()  # Should not call LLM when deterministic matches
        assert isinstance(result, EndosomalResult)
        assert result.output == "archive_now"


@patch("metabolon.enzymes.endosomal.synthesize")
def test_endosomal_categorize_deterministic_miss(mock_synthesize):
    """Test categorize falls back to synthesize when deterministic classification is empty."""
    # Ambiguous email that won't match deterministic rules
    email_text = """From: john@example.com
Subject: Hello

Just wanted to say hi.
"""
    mock_synthesize.return_value = "   borderline   "

    result = endosomal(action="categorize", email_text=email_text)

    mock_synthesize.assert_called_once()
    assert "Classify the following email" in mock_synthesize.call_args[0][0]
    assert "john@example.com" in mock_synthesize.call_args[0][0]
    assert isinstance(result, EndosomalResult)
    assert result.output == "borderline"


@patch("metabolon.enzymes.endosomal.synthesize")
def test_endosomal_categorize_llm_invalid_category(mock_synthesize):
    """Test categorize handles invalid category from LLM."""
    email_text = """From: john@example.com
Subject: Hello

Just wanted to say hi.
"""
    mock_synthesize.return_value = "   spam   "

    result = endosomal(action="categorize", email_text=email_text)

    assert isinstance(result, EndosomalResult)
    assert result.output == "Unclassified: spam"


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_archive_success(mock_invoke):
    """Test archive action calls invoke_organelle correctly."""
    mock_invoke.return_value = "Archived 2 messages"

    result = endosomal(action="archive", message_ids=["msg1", "msg2"])

    mock_invoke.assert_called_once_with("gog", ["gmail", "archive", "--force", "msg1", "msg2"], timeout=30)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Archived 2 messages" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_archive_default_message(mock_invoke):
    """Test archive returns default message when no result from invoke."""
    mock_invoke.return_value = ""

    result = endosomal(action="archive", message_ids=["msg1"])

    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Archived 1 message(s)." in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_mark_read_success(mock_invoke):
    """Test mark_read action calls invoke_organelle correctly."""
    mock_invoke.return_value = "Marked 3 messages as read"

    result = endosomal(action="mark_read", message_ids=["m1", "m2", "m3"])

    mock_invoke.assert_called_once_with("gog", ["gmail", "mark-read", "--force", "m1", "m2", "m3"], timeout=30)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Marked 3 messages as read" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_label_success(mock_invoke):
    """Test label action calls invoke_organelle correctly."""
    mock_invoke.return_value = "Created label 'Work'"

    result = endosomal(action="label", name="Work")

    mock_invoke.assert_called_once_with("gog", ["gmail", "labels", "create", "Work"], timeout=15)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Created label 'Work'" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_send_new_email_success(mock_invoke):
    """Test send action for new email calls invoke_organelle correctly."""
    mock_invoke.return_value = "Email sent successfully"

    result = endosomal(
        action="send",
        to="recipient@example.com",
        subject="Test Subject",
        body="This is the body",
        cc="cc@example.com",
        attach=["file1.txt", "file2.txt"]
    )

    expected_args = [
        "gmail", "send",
        "--to", "recipient@example.com",
        "--subject", "Test Subject",
        "--body", "This is the body",
        "--cc", "cc@example.com",
        "--attach", "file1.txt",
        "--attach", "file2.txt"
    ]
    mock_invoke.assert_called_once_with("gog", expected_args, timeout=60)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Email sent successfully" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_send_reply_success(mock_invoke):
    """Test send action as reply calls invoke_organelle correctly."""
    mock_invoke.return_value = "Reply sent"

    result = endosomal(
        action="send",
        reply_to_message_id="msg123",
        body="My reply here"
    )

    expected_args = [
        "gmail", "send",
        "--reply-to-message-id", "msg123",
        "--reply-all",
        "--quote",
        "--body", "My reply here"
    ]
    mock_invoke.assert_called_once_with("gog", expected_args, timeout=60)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Reply sent" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_filter_all_options(mock_invoke):
    """Test filter action with all options enabled calls correctly."""
    mock_invoke.return_value = "Filter created"

    result = endosomal(
        action="filter",
        from_sender="news@example.com",
        subject_pattern="Daily Update",
        add_label="News",
        archive=True,
        mark_read=True,
        dry_run=True
    )

    expected_args = [
        "gmail", "settings", "filters", "create",
        "--from", "news@example.com",
        "--subject", "Daily Update",
        "--add-label", "News",
        "--archive",
        "--mark-read",
        "--dry-run"
    ]
    mock_invoke.assert_called_once_with("gog", expected_args, timeout=15)
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "[DRY RUN] " in result.message
    assert "Filter created" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_filter_no_dry_run(mock_invoke):
    """Test filter action without dry-run doesn't add prefix."""
    mock_invoke.return_value = "Filter applied"

    result = endosomal(
        action="filter",
        from_sender="news@example.com",
        archive=True,
        dry_run=False
    )

    assert "[DRY RUN] " not in result.message
    assert "Filter applied" in result.message


def test_action_case_insensitive():
    """Test action is case-insensitive."""
    with patch("metabolon.enzymes.endosomal.invoke_organelle") as mock:
        mock.return_value = "Search results"
        result = endosomal(action="SEARCH", query="test")
        assert isinstance(result, EndosomalResult)
        assert result.output == "Search results"
        mock.assert_called_once()

    with patch("metabolon.enzymes.endosomal.invoke_organelle") as mock:
        mock.return_value = "Thread content"
        result = endosomal(action="Thread", thread_id="test")
        assert isinstance(result, EndosomalResult)
        assert result.output == "Thread content"
        mock.assert_called_once()


# Test the classification logic in endosomal_organelle directly
def test_extract_sender():
    """Test extract_sender handles various formats."""
    # With name and angle brackets
    email_text = "From: John Doe <john@example.com>\nSubject: Test"
    assert endosomal_organelle.extract_sender(email_text) == "john@example.com"

    # Without angle brackets
    email_text = "From: john@example.com\nSubject: Test"
    assert endosomal_organelle.extract_sender(email_text) == "john@example.com"

    # No From header
    email_text = "Subject: Test\nBody here"
    assert endosomal_organelle.extract_sender(email_text) == ""


def test_sender_is_automated():
    """Test sender_is_automated detects automated senders."""
    # No-reply at local
    assert endosomal_organelle.sender_is_automated("noreply@example.com") is True
    assert endosomal_organelle.sender_is_automated("no-reply@example.com") is True

    # Known automated domain
    assert endosomal_organelle.sender_is_automated("info@github.com") is True
    assert endosomal_organelle.sender_is_automated("news@sendgrid.net") is True

    # Not automated
    assert endosomal_organelle.sender_is_automated("john@example.com") is False
    assert endosomal_organelle.sender_is_automated("") is False


def test_extract_subject():
    """Test extract_subject extracts subject correctly."""
    email_text = "From: john@example.com\nSubject: This is a test\nBody"
    assert endosomal_organelle.extract_subject(email_text) == "This is a test"

    email_text = "From: john@example.com\nBody here"
    assert endosomal_organelle.extract_subject(email_text) == ""


def test_classify_subject_action_required():
    """Test classify_subject detects action required."""
    assert endosomal_organelle.classify_subject("[Action Required] Meeting today") == "action_required"
    assert endosomal_organelle.classify_subject("[URGENT] Finish report") == "action_required"


def test_classify_subject_archive_now():
    """Test classify_subject detects archive now."""
    assert endosomal_organelle.classify_subject("Invitation: Meeting with Bob") == "archive_now"
    assert endosomal_organelle.classify_subject("Updated Invitation: Team lunch") == "archive_now"


def test_classify_subject_monitor():
    """Test classify_subject detects monitor content."""
    assert endosomal_organelle.classify_subject("Weekly Digest for April") == "monitor"
    assert endosomal_organelle.classify_subject("Monthly Update") == "monitor"


def test_classify_subject_borderline():
    """Test classify_subject detects borderline content."""
    assert endosomal_organelle.classify_subject("Re: Your question") == "borderline"
    assert endosomal_organelle.classify_subject("Fwd: Meeting notes") == "borderline"


def test_classify_full_sender_automated():
    """Test full classification with automated sender."""
    email_text = """From: noreply@github.com
Subject: Your latest push

Your push to main was successful.
"""
    assert endosomal_organelle.classify(email_text) == "archive_now"


def test_classify_full_action_required_body():
    """Test full classification finds action required in body."""
    email_text = """From: boss@company.com
Subject: Update

We need this done by EOD today. It's urgent and requires your approval.
"""
    assert endosomal_organelle.classify(email_text) == "action_required"


def test_classify_full_archive_body():
    """Test full classification finds archive in body."""
    email_text = """From: newsletter@blog.com
Subject: New post this week

Click here to read the latest post. Unsubscribe at any time.
"""
    assert endosomal_organelle.classify(email_text) == "archive_now"


def test_classify_full_monitor_body():
    """Test full classification finds monitor in body."""
    email_text = """From: team@company.com
Subject: Team meeting notes

FYI, here are the minutes from today's meeting.
"""
    assert endosomal_organelle.classify(email_text) == "monitor"


def test_classify_full_borderline_body():
    """Test full classification finds borderline in body."""
    email_text = """From: colleague@company.com
Subject: Question

Could you please give me your thoughts on this when you have a chance?
"""
    assert endosomal_organelle.classify(email_text) == "borderline"


def test_classify_full_ambiguous():
    """Test full classification returns empty for ambiguous emails."""
    email_text = """From: john@example.com
Subject: Hello

Just checking in.
"""
    assert endosomal_organelle.classify(email_text) == ""


def test_endosomal_pipeline():
    """Test full endosomal pipeline returns correct structure."""
    email_text = """From: urgent@company.com
Subject: Approval needed

Please sign off on this budget by EOD.
"""
    result = endosomal_organelle.endosomal_pipeline(email_text)
    assert result["stage"] == "complete"
    assert result["category"] == "action_required"
    assert result["action"] is not None
    assert result["fate"] == "surface immediately"


# ---------------------------------------------------------------------------
# Additional coverage: organelle pass-2 short-circuit, empty subjects, edge cases
# ---------------------------------------------------------------------------


def test_classify_subject_empty():
    """classify_subject returns '' for empty string."""
    assert endosomal_organelle.classify_subject("") == ""


def test_classify_subject_no_match():
    """classify_subject returns '' for subject with no matching patterns."""
    assert endosomal_organelle.classify_subject("Regular subject line") == ""


def test_classify_pass2_short_circuit():
    """classify returns subject verdict at pass 2 when sender is not automated.

    This covers line 144 (return subject_verdict) in the organelle.
    """
    email_text = """From: alice@company.com
Subject: [URGENT] Server down

We need to fix this now.
"""
    assert endosomal_organelle.classify(email_text) == "action_required"


def test_classify_no_subject_header():
    """classify handles email with no Subject: header (empty subject at pass 2)."""
    email_text = """From: bob@company.com

Just wanted to check in with you.
"""
    # Falls through to body scan — "please" not present, but nothing else matches
    # "just wanted to" is not in any keyword list, so this should be ambiguous
    assert endosomal_organelle.classify(email_text) == ""


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_send_default_message(mock_invoke):
    """Test send returns default message when invoke_organelle returns empty."""
    mock_invoke.return_value = ""

    result = endosomal(action="send", to="a@b.com", subject="Hi", body="Hello")

    assert isinstance(result, EffectorResult)
    assert result.success
    assert result.message == "Email sent."


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_send_reply_only_body(mock_invoke):
    """Test send as reply with only body — no to/subject needed."""
    mock_invoke.return_value = "Reply sent"

    result = endosomal(action="send", reply_to_message_id="msg999", body="Noted, thanks")

    args = mock_invoke.call_args[0][1]
    assert "--reply-to-message-id" in args
    assert "msg999" in args
    assert "--body" in args
    assert "Noted, thanks" in args
    assert isinstance(result, EffectorResult)
    assert result.success


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_mark_read_default_message(mock_invoke):
    """Test mark_read returns default message when invoke returns empty."""
    mock_invoke.return_value = ""

    result = endosomal(action="mark_read", message_ids=["m1"])

    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Marked 1 message(s) as read." in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_label_default_message(mock_invoke):
    """Test label returns default message when invoke returns empty."""
    mock_invoke.return_value = ""

    result = endosomal(action="label", name="Projects")

    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Label created: Projects" in result.message


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_filter_subject_pattern_only(mock_invoke):
    """Test filter with only subject_pattern (no from_sender)."""
    mock_invoke.return_value = "Filter created"

    result = endosomal(
        action="filter",
        subject_pattern="Newsletter",
        add_label="Bulk",
        dry_run=False,
    )

    args = mock_invoke.call_args[0][1]
    assert "--subject" in args
    assert "--from" not in args
    assert isinstance(result, EffectorResult)
    assert result.success


@patch("metabolon.enzymes.endosomal.invoke_organelle")
def test_endosomal_filter_default_message(mock_invoke):
    """Test filter returns default message when invoke returns empty."""
    mock_invoke.return_value = ""

    result = endosomal(
        action="filter",
        from_sender="x@y.com",
        mark_read=True,
        dry_run=False,
    )

    assert isinstance(result, EffectorResult)
    assert result.success
    assert result.message == "Filter applied."


def test_endosomal_action_whitespace_padding():
    """Test action with leading/trailing whitespace is stripped."""
    with patch("metabolon.enzymes.endosomal.invoke_organelle") as mock:
        mock.return_value = "ok"
        result = endosomal(action="  search  ", query="test")
        assert isinstance(result, EndosomalResult)
        mock.assert_called_once()


@patch("metabolon.enzymes.endosomal.synthesize")
def test_endosomal_categorize_llm_valid_category_normalization(mock_synthesize):
    """Test categorize normalizes LLM output with dashes to underscores."""
    email_text = "From: a@b.com\nSubject: Test\nBody"
    mock_synthesize.return_value = "  action-required  "

    result = endosomal(action="categorize", email_text=email_text)

    assert isinstance(result, EndosomalResult)
    assert result.output == "action_required"


def test_endosomal_pipeline_with_borderline():
    """Test pipeline returns correct fate for borderline category."""
    email_text = """From: colleague@company.com
Subject: Re: Project update

Could you review this when you have a chance?
"""
    result = endosomal_organelle.endosomal_pipeline(email_text)
    assert result["stage"] == "complete"
    assert result["category"] == "borderline"
    assert result["fate"] == "batch for review"


def test_endosomal_pipeline_with_archive():
    """Test pipeline returns correct fate for archive_now category."""
    email_text = """From: noreply@github.com
Subject: Notification

Your issue was closed.
"""
    result = endosomal_organelle.endosomal_pipeline(email_text)
    assert result["stage"] == "complete"
    assert result["category"] == "archive_now"
    assert result["fate"] == "archive silently"


def test_endosomal_pipeline_with_monitor():
    """Test pipeline returns correct fate for monitor category."""
    email_text = """From: team@company.com
Subject: FYI: New policy

FYI, just wanted to share this update with you.
"""
    result = endosomal_organelle.endosomal_pipeline(email_text)
    assert result["stage"] == "complete"
    assert result["category"] == "monitor"
    assert result["fate"] == "note and archive"


def test_endosomal_pipeline_ambiguous_defaults_to_archive():
    """Test pipeline defaults to 'archive silently' for unclassified email."""
    email_text = """From: john@example.com
Subject: Hello

Just checking in.
"""
    result = endosomal_organelle.endosomal_pipeline(email_text)
    assert result["stage"] == "complete"
    assert result["category"] == ""
    assert result["action"] is None
    assert result["fate"] == "archive silently"
