"""Tests for endosomal organelle — email classification and triage."""

from metabolon.organelles.endosomal import (
    extract_sender,
    sender_is_automated,
    extract_subject,
    classify_subject,
    classify,
    endosomal_pipeline,
    STAGES,
    CATEGORIES,
)


# --- Constants ---

def test_stages():
    assert STAGES == ("triage", "process", "route")

def test_categories():
    assert "action_required" in CATEGORIES
    assert "archive_now" in CATEGORIES


# --- extract_sender ---

def test_extract_sender_angle_brackets():
    assert extract_sender("From: John <john@example.com>\nBody") == "john@example.com"

def test_extract_sender_plain():
    assert extract_sender("From: alice@example.com\nBody") == "alice@example.com"

def test_extract_sender_missing():
    assert extract_sender("Subject: hello\nBody") == ""

def test_extract_sender_case_insensitive():
    assert extract_sender("from: Bob@EXAMPLE.COM\n") == "bob@example.com"


# --- sender_is_automated ---

def test_noreply():
    assert sender_is_automated("noreply@company.com") is True

def test_no_reply_hyphen():
    assert sender_is_automated("no-reply@company.com") is True

def test_linkedin():
    assert sender_is_automated("updates@linkedin.com") is True

def test_github():
    assert sender_is_automated("notifications@github.com") is True

def test_normal_sender():
    assert sender_is_automated("john@example.com") is False

def test_empty_sender():
    assert sender_is_automated("") is False


# --- extract_subject ---

def test_extract_subject():
    assert extract_subject("From: x\nSubject: Hello World\nBody") == "Hello World"

def test_extract_subject_missing():
    assert extract_subject("From: x\nBody") == ""


# --- classify_subject ---

def test_subject_action_required():
    assert classify_subject("[Action Required] Review document") == "action_required"

def test_subject_urgent():
    assert classify_subject("[URGENT] Server down") == "action_required"

def test_subject_invitation():
    assert classify_subject("Invitation: Team meeting") == "archive_now"

def test_subject_digest():
    assert classify_subject("Weekly digest: AI News") == "monitor"

def test_subject_reply():
    assert classify_subject("Re: Budget discussion") == "borderline"

def test_subject_forward():
    assert classify_subject("Fwd: Interesting article") == "borderline"

def test_subject_normal():
    assert classify_subject("Hello there") == ""


# --- classify (full pipeline) ---

def test_classify_automated_sender():
    assert classify("From: noreply@amazonses.com\nSubject: Receipt\nBody") == "archive_now"

def test_classify_action_body():
    assert classify("From: boss@work.com\nSubject: Task\nPlease respond by end of day") == "action_required"

def test_classify_newsletter():
    assert classify("From: news@blog.com\nSubject: Update\nClick here to unsubscribe") == "archive_now"

def test_classify_monitor():
    assert classify("From: team@work.com\nSubject: Info\nFYI, just a heads up about the schedule change") == "monitor"

def test_classify_borderline():
    assert classify("From: colleague@work.com\nSubject: Question\nCould you look at this?") == "borderline"

def test_classify_ambiguous():
    assert classify("From: someone@unknown.com\nSubject: Hey\nJust a note.") == ""


# --- endosomal_pipeline ---

def test_pipeline_action():
    result = endosomal_pipeline("From: boss@work.com\nSubject: [Action Required] Review\nPlease review ASAP")
    assert result["category"] == "action_required"
    assert result["fate"] == "surface immediately"
    assert result["stage"] == "complete"

def test_pipeline_archive():
    result = endosomal_pipeline("From: noreply@github.com\nSubject: Notification\nBody")
    assert result["category"] == "archive_now"
    assert result["fate"] == "archive silently"

def test_pipeline_ambiguous():
    result = endosomal_pipeline("From: x@y.com\nSubject: Hi\nGeneric text")
    assert result["category"] == ""
    assert result["fate"] == "archive silently"
    assert result["action"] is None
