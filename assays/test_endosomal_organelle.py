"""Tests for metabolon/organelles/endosomal.py - email classification logic."""

import pytest

from metabolon.organelles.endosomal import (
    STAGES,
    CATEGORIES,
    extract_sender,
    sender_is_automated,
    extract_subject,
    classify_subject,
    classify,
    endosomal_pipeline,
    CLASSIFY_PROMPT_TMPL,
)


# ── Constants tests ─────────────────────────────────────────────────────


def test_stages_tuple():
    """STAGES contains expected maturation stages."""
    assert STAGES == ("triage", "process", "route")


def test_categories_tuple():
    """CATEGORIES contains expected classification categories."""
    assert "action_required" in CATEGORIES
    assert "borderline" in CATEGORIES
    assert "monitor" in CATEGORIES
    assert "archive_now" in CATEGORIES


def test_categories_count():
    """CATEGORIES has exactly 4 categories."""
    assert len(CATEGORIES) == 4


# ── extract_sender tests ─────────────────────────────────────────────────


def test_extract_sender_simple():
    """extract_sender extracts simple email address."""
    email = "From: test@example.com\nSubject: Test"
    assert extract_sender(email) == "test@example.com"


def test_extract_sender_with_name():
    """extract_sender extracts address from 'Name <addr>' format."""
    email = "From: John Doe <john@example.com>\nSubject: Test"
    assert extract_sender(email) == "john@example.com"


def test_extract_sender_lowercase():
    """extract_sender returns lowercase address."""
    email = "From: John@Example.COM\nSubject: Test"
    assert extract_sender(email) == "john@example.com"


def test_extract_sender_case_insensitive_header():
    """extract_sender handles case-insensitive 'From:' header."""
    email = "from: test@example.com\nSubject: Test"
    assert extract_sender(email) == "test@example.com"


def test_extract_sender_no_from_header():
    """extract_sender returns empty string if no From header."""
    email = "Subject: Test\nBody content"
    assert extract_sender(email) == ""


def test_extract_sender_with_whitespace():
    """extract_sender handles whitespace in From header."""
    email = "From:   test@example.com  \nSubject: Test"
    assert extract_sender(email) == "test@example.com"


def test_extract_sender_multiple_lines():
    """extract_sender finds From header among multiple lines."""
    email = "To: recipient@example.com\nFrom: sender@example.com\nSubject: Test"
    assert extract_sender(email) == "sender@example.com"


# ── sender_is_automated tests ───────────────────────────────────────────


def test_sender_is_automated_noreply():
    """sender_is_automated returns True for noreply addresses."""
    assert sender_is_automated("noreply@example.com") is True
    assert sender_is_automated("no-reply@example.com") is True


def test_sender_is_automated_donotreply():
    """sender_is_automated returns True for do-not-reply addresses."""
    assert sender_is_automated("donotreply@example.com") is True
    assert sender_is_automated("do-not-reply@example.com") is True


def test_sender_is_automated_amazon_ses():
    """sender_is_automated returns True for Amazon SES."""
    assert sender_is_automated("anything@amazonses.com") is True


def test_sender_is_automated_sendgrid():
    """sender_is_automated returns True for SendGrid."""
    assert sender_is_automated("alerts@sendgrid.net") is True


def test_sender_is_automated_github():
    """sender_is_automated returns True for GitHub notifications."""
    assert sender_is_automated("notifications@github.com") is True


def test_sender_is_automated_linkedin():
    """sender_is_automated returns True for LinkedIn."""
    assert sender_is_automated("messages@linkedin.com") is True


def test_sender_is_automated_google_calendar():
    """sender_is_automated returns True for Google Calendar."""
    assert sender_is_automated("calendar@mail.google.com") is True


def test_sender_is_automated_regular_sender():
    """sender_is_automated returns False for regular addresses."""
    assert sender_is_automated("john@gmail.com") is False
    assert sender_is_automated("jane@company.com") is False


def test_sender_is_automated_empty_sender():
    """sender_is_automated returns False for empty sender."""
    assert sender_is_automated("") is False


def test_sender_is_automated_no_at_sign():
    """sender_is_automated handles addresses without @."""
    assert sender_is_automated("notanemail") is False


# ── extract_subject tests ────────────────────────────────────────────────


def test_extract_subject_simple():
    """extract_subject extracts subject line."""
    email = "From: test@example.com\nSubject: Hello World\nBody"
    assert extract_subject(email) == "Hello World"


def test_extract_subject_case_insensitive():
    """extract_subject handles case-insensitive 'Subject:' header."""
    email = "subject: lowercase subject\nBody"
    assert extract_subject(email) == "lowercase subject"


def test_extract_subject_no_subject():
    """extract_subject returns empty string if no Subject header."""
    email = "From: test@example.com\nBody content"
    assert extract_subject(email) == ""


def test_extract_subject_preserves_whitespace():
    """extract_subject preserves internal whitespace."""
    email = "Subject: Re: Meeting Tomorrow\nBody"
    assert extract_subject(email) == "Re: Meeting Tomorrow"


# ── classify_subject tests ───────────────────────────────────────────────


def test_classify_subject_action_required():
    """classify_subject returns action_required for urgency markers."""
    assert classify_subject("[ACTION REQUIRED] Please respond") == "action_required"
    assert classify_subject("[URGENT] Important update") == "action_required"


def test_classify_subject_archive_invitation():
    """classify_subject returns archive_now for calendar invitations."""
    assert classify_subject("Invitation: Meeting") == "archive_now"
    assert classify_subject("Updated invitation: Rescheduled") == "archive_now"


def test_classify_subject_monitor_digest():
    """classify_subject returns monitor for digest content."""
    assert classify_subject("Weekly digest") == "monitor"
    assert classify_subject("Monthly newsletter digest") == "monitor"


def test_classify_subject_borderline_reply():
    """classify_subject returns borderline for reply/forward threads."""
    assert classify_subject("Re: Previous discussion") == "borderline"
    assert classify_subject("Fwd: Important message") == "borderline"


def test_classify_subject_empty():
    """classify_subject returns empty string for empty subject."""
    assert classify_subject("") == ""


def test_classify_subject_no_pattern():
    """classify_subject returns empty string when no pattern matches."""
    assert classify_subject("Regular email subject") == ""


def test_classify_subject_case_insensitive():
    """classify_subject is case-insensitive."""
    assert classify_subject("[ACTION REQUIRED]") == "action_required"
    assert classify_subject("[urgent]") == "action_required"


# ── classify tests ───────────────────────────────────────────────────────


def test_classify_sender_automated():
    """classify returns archive_now for automated senders."""
    email = "From: noreply@amazonses.com\nSubject: Notification\nBody"
    assert classify(email) == "archive_now"


def test_classify_subject_action():
    """classify returns action_required for urgent subjects."""
    email = "From: boss@company.com\nSubject: [URGENT] Please review\nBody"
    assert classify(email) == "action_required"


def test_classify_body_action_keywords():
    """classify returns action_required for action keywords in body."""
    email = "From: boss@company.com\nSubject: Project\n\nThis is urgent, please respond."
    assert classify(email) == "action_required"


def test_classify_body_deadline():
    """classify returns action_required for deadline keywords."""
    email = "From: pm@company.com\nSubject: Status\n\nDeadline is tomorrow."
    assert classify(email) == "action_required"


def test_classify_body_approval_needed():
    """classify returns action_required for approval keywords."""
    email = "From: hr@company.com\nSubject: Request\n\nApproval needed for time off."
    assert classify(email) == "action_required"


def test_classify_body_archive_keywords():
    """classify returns archive_now for archive keywords."""
    email = "From: marketing@company.com\nSubject: Update\n\nClick here to unsubscribe."
    assert classify(email) == "archive_now"


def test_classify_body_newsletter():
    """classify returns archive_now for newsletter markers."""
    email = "From: news@company.com\nSubject: Newsletter\n\nThis is a newsletter."
    assert classify(email) == "archive_now"


def test_classify_body_marketing():
    """classify returns archive_now for marketing content."""
    email = "From: promo@shop.com\nSubject: Sale\n\nSpecial offer just for you!"
    assert classify(email) == "archive_now"


def test_classify_body_transaction_alert():
    """classify returns archive_now for transaction alerts."""
    email = "From: bank@bank.com\nSubject: Alert\n\nTransaction alert: $50 charged."
    assert classify(email) == "archive_now"


def test_classify_body_security_alert():
    """classify returns archive_now for security alerts."""
    email = "From: security@service.com\nSubject: Security\n\nSecurity alert: login attempt."
    assert classify(email) == "archive_now"


def test_classify_body_monitor_fyi():
    """classify returns monitor for FYI content."""
    email = "From: team@company.com\nSubject: Update\n\nFYI, the meeting was moved."
    assert classify(email) == "monitor"


def test_classify_body_monitor_heads_up():
    """classify returns monitor for heads-up content."""
    email = "From: team@company.com\nSubject: Note\n\nHeads up, client visiting tomorrow."
    assert classify(email) == "monitor"


def test_classify_body_monitor_announcement():
    """classify returns monitor for announcements."""
    email = "From: all@company.com\nSubject: Announcement\n\nAnnouncement: New policy."
    assert classify(email) == "monitor"


def test_classify_body_borderline_please():
    """classify returns borderline for polite requests."""
    email = "From: colleague@company.com\nSubject: Quick question\n\nPlease take a look when you can."
    assert classify(email) == "borderline"


def test_classify_body_borderline_feedback():
    """classify returns borderline for feedback requests."""
    email = "From: team@company.com\nSubject: Draft\n\nI'd appreciate your feedback on this."
    assert classify(email) == "borderline"


def test_classify_ambiguous_returns_empty():
    """classify returns empty string for genuinely ambiguous emails."""
    email = "From: someone@company.com\nSubject: Hello\n\nJust wanted to say hi."
    assert classify(email) == ""


def test_classify_prioritizes_sender_over_subject():
    """classify checks sender (pass 1) before subject (pass 2)."""
    # Sender is automated, should return archive_now even with urgent subject
    email = "From: noreply@amazonses.com\nSubject: [URGENT]\nBody"
    assert classify(email) == "archive_now"


def test_classify_prioritizes_subject_over_body():
    """classify checks subject (pass 2) before body (pass 3)."""
    # Subject has action marker, should return action_required
    email = "From: someone@company.com\nSubject: [ACTION REQUIRED]\nunsubscribe link here"
    assert classify(email) == "action_required"


# ── endosomal_pipeline tests ─────────────────────────────────────────────


def test_endosomal_pipeline_action_required():
    """endosomal_pipeline handles action_required category."""
    email = "From: boss@company.com\nSubject: [URGENT]\n\nPlease review this document."
    result = endosomal_pipeline(email)

    assert result["stage"] == "complete"
    assert result["category"] == "action_required"
    assert result["fate"] == "surface immediately"
    assert result["action"] is not None


def test_endosomal_pipeline_archive_now():
    """endosomal_pipeline handles archive_now category."""
    email = "From: noreply@amazonses.com\nSubject: Notification\nBody"
    result = endosomal_pipeline(email)

    assert result["stage"] == "complete"
    assert result["category"] == "archive_now"
    assert result["fate"] == "archive silently"
    assert result["action"] is None


def test_endosomal_pipeline_monitor():
    """endosomal_pipeline handles monitor category."""
    email = "From: team@company.com\nSubject: Update\n\nFYI, meeting moved."
    result = endosomal_pipeline(email)

    assert result["stage"] == "complete"
    assert result["category"] == "monitor"
    assert result["fate"] == "note and archive"
    assert result["action"] is None


def test_endosomal_pipeline_borderline():
    """endosomal_pipeline handles borderline category."""
    email = "From: team@company.com\nSubject: Re: Question\n\nPlease review when you can."
    result = endosomal_pipeline(email)

    assert result["stage"] == "complete"
    assert result["category"] == "borderline"
    assert result["fate"] == "batch for review"


def test_endosomal_pipeline_ambiguous():
    """endosomal_pipeline handles ambiguous emails."""
    email = "From: someone@company.com\nSubject: Hello\n\nJust saying hi."
    result = endosomal_pipeline(email)

    assert result["stage"] == "complete"
    assert result["category"] == ""
    assert result["fate"] == "archive silently"


def test_endosomal_pipeline_extracts_action():
    """endosomal_pipeline extracts action line for action_required."""
    email = "From: boss@company.com\nSubject: Review\n\nPlease review this.\n\nThanks."
    result = endosomal_pipeline(email)

    assert result["category"] == "action_required"
    assert "review" in result["action"].lower()


def test_endosomal_pipeline_finds_question_line():
    """endosomal_pipeline finds question line for action extraction."""
    email = "From: boss@company.com\nSubject: [URGENT]\n\nCan you help with this?\nThanks."
    result = endosomal_pipeline(email)

    assert result["category"] == "action_required"
    assert "?" in result["action"]


# ── CLASSIFY_PROMPT_TMPL tests ───────────────────────────────────────────


def test_classify_prompt_tmpl_exists():
    """CLASSIFY_PROMPT_TMPL is defined."""
    assert CLASSIFY_PROMPT_TMPL is not None
    assert isinstance(CLASSIFY_PROMPT_TMPL, str)


def test_classify_prompt_tmpl_contains_categories():
    """CLASSIFY_PROMPT_TMPL mentions all categories."""
    for cat in CATEGORIES:
        assert cat in CLASSIFY_PROMPT_TMPL


def test_classify_prompt_tmpl_has_placeholder():
    """CLASSIFY_PROMPT_TMPL has {email_text} placeholder."""
    assert "{email_text}" in CLASSIFY_PROMPT_TMPL


def test_classify_prompt_tmpl_format():
    """CLASSIFY_PROMPT_TMPL can be formatted with email text."""
    formatted = CLASSIFY_PROMPT_TMPL.format(email_text="Test email content")
    assert "Test email content" in formatted
