from __future__ import annotations

"""Tests for endosomal — email classification and triage logic.

Covers:
  - extract_sender with various header formats
  - sender_is_automated for known automated sender patterns
  - extract_subject header parsing
  - classify_subject subject-line pattern matching
  - classify three-pass cascade (sender → subject → body)
  - endosomal_pipeline full triage → process → fate flow
"""


from metabolon.organelles.endosomal import (
    CATEGORIES,
    CLASSIFY_PROMPT_TMPL,
    STAGES,
    classify,
    classify_subject,
    endosomal_pipeline,
    extract_sender,
    extract_subject,
    sender_is_automated,
)

# ── Constants ────────────────────────────────────────────────────────────────


class TestConstants:
    def test_stages_ordered(self):
        """Stages should be in maturation order."""
        assert STAGES == ("triage", "process", "route")

    def test_categories_defined(self):
        """Categories should include all four classification buckets."""
        assert "action_required" in CATEGORIES
        assert "borderline" in CATEGORIES
        assert "monitor" in CATEGORIES
        assert "archive_now" in CATEGORIES


# ── extract_sender ────────────────────────────────────────────────────────────


class TestExtractSender:
    def test_simple_address(self):
        """Plain email address after From:."""
        email = "From: alice@example.com\nSubject: Test"
        assert extract_sender(email) == "alice@example.com"

    def test_angle_bracket_address(self):
        """Address in angle brackets with display name."""
        email = "From: Alice Smith <alice@example.com>\nSubject: Hello"
        assert extract_sender(email) == "alice@example.com"

    def test_case_normalization(self):
        """Sender should be lowercased."""
        email = "From: BOB@Example.COM"
        assert extract_sender(email) == "bob@example.com"

    def test_missing_from_header(self):
        """Return empty string if no From header."""
        email = "Subject: No sender\nTo: bob@example.com"
        assert extract_sender(email) == ""

    def test_from_in_body_not_header(self):
        """Only match From: at line start, not in body."""
        email = "Subject: Test\n\nTalk about from: something"
        assert extract_sender(email) == ""

    def test_multiline_headers(self):
        """Find From: among multiple headers."""
        email = "To: bob@example.com\nFrom: carol@example.com\nDate: Today"
        assert extract_sender(email) == "carol@example.com"


# ── sender_is_automated ───────────────────────────────────────────────────────


class TestSenderIsAutomated:
    def test_noreply_local_part(self):
        """noreply@anything is automated."""
        assert sender_is_automated("noreply@example.com") is True
        assert sender_is_automated("no-reply@example.com") is True
        assert sender_is_automated("donotreply@example.com") is True

    def test_automated_domain(self):
        """Known automated sender domains."""
        assert sender_is_automated("anything@amazonses.com") is True
        assert sender_is_automated("alerts@sendgrid.net") is True
        assert sender_is_automated("news@mailchimp.com") is True
        assert sender_is_automated("notify@github.com") is True
        assert sender_is_automated("bot@linkedin.com") is True

    def test_google_calendar_domain(self):
        """Google calendar/mail automation domains."""
        assert sender_is_automated("me@mail.google.com") is True
        assert sender_is_automated("me@calendar.google.com") is True

    def test_regular_sender_not_automated(self):
        """Normal human senders are not flagged."""
        assert sender_is_automated("alice@company.com") is False
        assert sender_is_automated("bob@gmail.com") is False

    def test_empty_sender_not_automated(self):
        """Empty string is not automated."""
        assert sender_is_automated("") is False

    def test_malformed_sender(self):
        """Address without @ is not automated."""
        assert sender_is_automated("not-an-address") is False


# ── extract_subject ───────────────────────────────────────────────────────────


class TestExtractSubject:
    def test_simple_subject(self):
        """Basic Subject: header."""
        email = "From: a@b.com\nSubject: Hello World"
        assert extract_subject(email) == "Hello World"

    def test_case_insensitive_header(self):
        """Subject header matching is case-insensitive."""
        email = "subject: Lowercase header"
        assert extract_subject(email) == "Lowercase header"

    def test_missing_subject(self):
        """Return empty string if no Subject header."""
        email = "From: a@b.com\n\nBody text"
        assert extract_subject(email) == ""

    def test_subject_with_colon(self):
        """Subject can contain colons."""
        email = "Subject: Re: Fwd: Important: Read this"
        assert extract_subject(email) == "Re: Fwd: Important: Read this"


# ── classify_subject ──────────────────────────────────────────────────────────


class TestClassifySubject:
    def test_action_required_marker(self):
        """[action required] and [urgent] trigger action_required."""
        assert classify_subject("[Action Required] Review") == "action_required"
        assert classify_subject("Meeting [URGENT]") == "action_required"

    def test_invitation_archive(self):
        """Calendar invitations are archive_now."""
        assert classify_subject("Invitation: Weekly sync") == "archive_now"
        assert classify_subject("Updated invitation: Rescheduled") == "archive_now"

    def test_digest_monitor(self):
        """Digest/periodic subjects are monitor."""
        assert classify_subject("Your weekly digest") == "monitor"
        assert classify_subject("Monthly report") == "monitor"

    def test_reply_borderline(self):
        """Re: and Fwd: threads are borderline."""
        assert classify_subject("Re: Previous discussion") == "borderline"
        assert classify_subject("Fwd: Check this out") == "borderline"

    def test_empty_subject(self):
        """Empty subject returns empty string."""
        assert classify_subject("") == ""

    def test_no_pattern(self):
        """Subject without patterns returns empty string."""
        assert classify_subject("Regular meeting tomorrow") == ""


# ── classify (three-pass cascade) ─────────────────────────────────────────────


class TestClassify:
    def test_sender_automated_short_circuits(self):
        """Automated sender returns archive_now before subject/body checks."""
        email = (
            "From: noreply@sendgrid.net\nSubject: [URGENT] Action needed!\n\nPlease respond ASAP!"
        )
        assert classify(email) == "archive_now"

    def test_subject_pattern_short_circuits(self):
        """Subject pattern fires before body scan."""
        email = "From: human@example.com\nSubject: [Action Required] Review\n\nJust checking in."
        assert classify(email) == "action_required"

    def test_body_action_keywords(self):
        """Body keywords trigger action_required."""
        email = "From: boss@company.com\nSubject: Project\n\nThis is urgent, please respond."
        assert classify(email) == "action_required"

    def test_body_archive_keywords(self):
        """Body keywords trigger archive_now."""
        email = "From: newsletter@news.com\nSubject: Updates\n\nClick here to unsubscribe."
        assert classify(email) == "archive_now"

    def test_body_monitor_keywords(self):
        """Body keywords trigger monitor."""
        email = "From: team@company.com\nSubject: Update\n\nFYI, the project is on track."
        assert classify(email) == "monitor"

    def test_body_borderline_keywords(self):
        """Body keywords trigger borderline."""
        email = "From: colleague@company.com\nSubject: Question\n\nCould you help with this?"
        assert classify(email) == "borderline"

    def test_ambiguous_returns_empty(self):
        """Truly ambiguous emails return empty string for symbiont fallback."""
        email = "From: someone@company.com\nSubject: Hello\n\nJust saying hi."
        assert classify(email) == ""

    def test_deadline_action(self):
        """Deadline keyword triggers action_required."""
        email = "From: pm@company.com\nSubject: Project\n\nDeadline is tomorrow."
        assert classify(email) == "action_required"

    def test_approval_needed_action(self):
        """Approval keywords trigger action_required."""
        email = "From: system@company.com\nSubject: Request\n\nYour approval needed."
        assert classify(email) == "action_required"

    def test_security_alert_archive(self):
        """Security alerts are archive_now (automated)."""
        email = (
            "From: security@example.com\nSubject: Alert\n\nSecurity alert: login attempt detected."
        )
        assert classify(email) == "archive_now"


# ── endosomal_pipeline ────────────────────────────────────────────────────────


class TestEndosomalPipeline:
    def test_action_required_pipeline(self):
        """action_required emails surface immediately with action extracted."""
        email = "From: boss@company.com\nSubject: Review\n\nPlease review the attached proposal?"
        result = endosomal_pipeline(email)
        assert result["stage"] == "complete"
        assert result["category"] == "action_required"
        assert result["fate"] == "surface immediately"
        assert "Please review" in result["action"]

    def test_archive_now_pipeline(self):
        """archive_now emails are archived silently."""
        email = "From: noreply@sendgrid.net\nSubject: Notification\n\nAutomated message."
        result = endosomal_pipeline(email)
        assert result["category"] == "archive_now"
        assert result["fate"] == "archive silently"
        assert result["action"] is None

    def test_monitor_pipeline(self):
        """monitor emails are noted and archived."""
        email = "From: team@company.com\nSubject: Update\n\nFYI, all good."
        result = endosomal_pipeline(email)
        assert result["category"] == "monitor"
        assert result["fate"] == "note and archive"
        assert result["action"] is None

    def test_borderline_pipeline(self):
        """borderline emails are batched for review."""
        email = "From: peer@company.com\nSubject: Question\n\nCould you help?"
        result = endosomal_pipeline(email)
        assert result["category"] == "borderline"
        assert result["fate"] == "batch for review"
        assert result["action"] is None

    def test_ambiguous_pipeline(self):
        """Ambiguous emails default to archive silently."""
        email = "From: someone@company.com\nSubject: Hello\n\nJust saying hi."
        result = endosomal_pipeline(email)
        assert result["category"] == ""
        assert result["fate"] == "archive silently"

    def test_action_extraction_prefers_question(self):
        """Action extraction prefers lines with questions."""
        email = "From: boss@company.com\nSubject: Urgent\n\nHere's context.\nCan you approve this?\nThanks."
        result = endosomal_pipeline(email)
        assert "Can you approve" in result["action"]

    def test_action_extraction_fallback_to_first_line(self):
        """If no question, action falls back to first line."""
        email = "From: boss@company.com\nSubject: Urgent\n\nPlease review the attached.\nThanks."
        result = endosomal_pipeline(email)
        assert result["action"] == "Please review the attached."


# ── CLASSIFY_PROMPT_TMPL ───────────────────────────────────────────────────────


class TestClassifyPromptTmpl:
    def test_template_includes_email_placeholder(self):
        """Prompt template has {email_text} placeholder."""
        assert "{email_text}" in CLASSIFY_PROMPT_TMPL

    def test_template_lists_all_categories(self):
        """Prompt template mentions all four categories."""
        assert "action_required" in CLASSIFY_PROMPT_TMPL
        assert "borderline" in CLASSIFY_PROMPT_TMPL
        assert "monitor" in CLASSIFY_PROMPT_TMPL
        assert "archive_now" in CLASSIFY_PROMPT_TMPL

    def test_template_format(self):
        """Template can be formatted with email text."""
        formatted = CLASSIFY_PROMPT_TMPL.format(email_text="Test email body")
        assert "Test email body" in formatted
