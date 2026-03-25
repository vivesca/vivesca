"""Tests for endosomal deterministic classifier.

Biology: glycolysis does not require a symbiont (LLM). These tests
verify that the three-pass membrane cascade (sender → subject → body)
classifies correctly and short-circuits as early as possible.
"""

import pytest

from metabolon.tools.endosomal import (
    _classify,
    _classify_subject,
    _extract_sender,
    _extract_subject,
    _sender_is_automated,
)

# ---------------------------------------------------------------------------
# _extract_sender
# ---------------------------------------------------------------------------


class TestExtractSender:
    def test_angle_bracket_form(self):
        text = "From: Alice Smith <alice@example.com>\nSubject: Hi"
        assert _extract_sender(text) == "alice@example.com"

    def test_bare_address_form(self):
        text = "From: noreply@github.com\nSubject: Your PR"
        assert _extract_sender(text) == "noreply@github.com"

    def test_case_insensitive_header(self):
        text = "FROM: Bob <bob@domain.org>\nSubject: Test"
        assert _extract_sender(text) == "bob@domain.org"

    def test_returns_lowercase(self):
        text = "From: UPPER@EXAMPLE.COM\nBody text"
        assert _extract_sender(text) == "upper@example.com"

    def test_no_from_header(self):
        text = "Subject: No headers here\nJust body text."
        assert _extract_sender(text) == ""

    def test_from_not_in_body(self):
        # "from:" appearing mid-body should not be extracted as sender
        text = "Subject: Update\n\nHi, this note is from: the team."
        # The body line starts with whitespace after subject, so it won't match
        # since we check strip().lower().startswith("from:")
        # This message has no From: header so returns empty
        assert _extract_sender(text) == ""


# ---------------------------------------------------------------------------
# _sender_is_automated
# ---------------------------------------------------------------------------


class TestSenderIsAutomated:
    @pytest.mark.parametrize(
        "sender",
        [
            "noreply@example.com",
            "no-reply@someservice.com",
            "donotreply@corp.io",
            "do-not-reply@alerts.com",
            "do_not_reply@updates.com",
        ],
    )
    def test_auto_local_parts(self, sender):
        assert _sender_is_automated(sender) is True

    @pytest.mark.parametrize(
        "sender",
        [
            "notifications@linkedin.com",
            "noreply@github.com",
            "updates@notion.so",
            "calendar-notification@mail.google.com",
            "invite@calendar.google.com",
            "bounce@amazonses.com",
            "alerts@sendgrid.net",
            "news@mailchimp.com",
            "campaign@constantcontact.com",
        ],
    )
    def test_auto_domains(self, sender):
        assert _sender_is_automated(sender) is True

    @pytest.mark.parametrize(
        "sender",
        [
            "alice@example.com",
            "boss@mycompany.com",
            "teammate@gmail.com",
            "",
        ],
    )
    def test_non_automated(self, sender):
        assert _sender_is_automated(sender) is False


# ---------------------------------------------------------------------------
# _extract_subject
# ---------------------------------------------------------------------------


class TestExtractSubject:
    def test_basic_subject(self):
        text = "From: a@b.com\nSubject: Hello World\n\nBody"
        assert _extract_subject(text) == "Hello World"

    def test_subject_case_insensitive(self):
        text = "SUBJECT: Test\nBody"
        assert _extract_subject(text) == "Test"

    def test_no_subject(self):
        text = "From: a@b.com\n\nJust a body."
        assert _extract_subject(text) == ""


# ---------------------------------------------------------------------------
# _classify_subject
# ---------------------------------------------------------------------------


class TestClassifySubject:
    def test_action_required_tag(self):
        assert _classify_subject("[Action Required] Please confirm") == "action_required"

    def test_urgent_tag(self):
        assert _classify_subject("[Urgent] System alert") == "action_required"

    def test_invitation_prefix(self):
        assert _classify_subject("Invitation: Team Standup @ 10am") == "archive_now"

    def test_updated_invitation_prefix(self):
        assert _classify_subject("Updated invitation: Sprint Planning") == "archive_now"

    def test_digest_in_subject(self):
        assert _classify_subject("Your Weekly Digest") == "monitor"

    def test_weekly_in_subject(self):
        assert _classify_subject("Weekly Engineering Update") == "monitor"

    def test_monthly_in_subject(self):
        assert _classify_subject("Monthly Report - February") == "monitor"

    def test_re_prefix(self):
        assert _classify_subject("Re: Project timeline") == "borderline"

    def test_fwd_prefix(self):
        assert _classify_subject("Fwd: Check this out") == "borderline"

    def test_no_match(self):
        assert _classify_subject("Lunch tomorrow?") == ""

    def test_empty_subject(self):
        assert _classify_subject("") == ""


# ---------------------------------------------------------------------------
# _classify — full cascade
# ---------------------------------------------------------------------------


class TestClassify:
    # -- Pass 1: sender domain short-circuit --

    def test_noreply_sender_archives_immediately(self):
        email = "From: noreply@github.com\nSubject: Your PR was merged\n\nBody text."
        assert _classify(email) == "archive_now"

    def test_linkedin_notification_archived(self):
        email = "From: notifications@linkedin.com\nSubject: Alice commented on your post\n\nSee who's commenting."
        assert _classify(email) == "archive_now"

    def test_sendgrid_archived(self):
        email = "From: bounce@sendgrid.net\nSubject: Your receipt\n\nThank you for your order."
        assert _classify(email) == "archive_now"

    def test_calendar_google_archived(self):
        email = "From: invite@calendar.google.com\nSubject: Team meeting\n\nYou have been invited."
        assert _classify(email) == "archive_now"

    # -- Pass 2: subject pattern --

    def test_action_required_subject_tag(self):
        email = "From: alice@example.com\nSubject: [Action Required] Sign the doc\n\nPlease sign."
        assert _classify(email) == "action_required"

    def test_urgent_subject_tag(self):
        email = "From: boss@company.com\nSubject: [Urgent] Server down\n\nFix it now."
        assert _classify(email) == "action_required"

    def test_invitation_subject_archived(self):
        email = "From: alice@company.com\nSubject: Invitation: Quarterly Review\n\nYou're invited."
        assert _classify(email) == "archive_now"

    def test_updated_invitation_archived(self):
        email = "From: alice@company.com\nSubject: Updated invitation: Kickoff meeting\n\nTime changed."
        assert _classify(email) == "archive_now"

    def test_digest_subject_monitor(self):
        email = "From: newsletter@company.com\nSubject: Weekly Digest\n\nHere's what happened."
        assert _classify(email) == "monitor"

    def test_re_subject_borderline(self):
        email = "From: bob@example.com\nSubject: Re: Project deadline\n\nSounds good."
        assert _classify(email) == "borderline"

    def test_fwd_subject_borderline(self):
        email = (
            "From: bob@example.com\nSubject: Fwd: Interesting article\n\nThought you'd like this."
        )
        assert _classify(email) == "borderline"

    # -- Pass 3: body keywords --

    def test_body_action_required_keyword(self):
        email = (
            "From: alice@example.com\nSubject: Meeting\n\nThis is urgent, please respond by EOD."
        )
        assert _classify(email) == "action_required"

    def test_body_archive_keyword(self):
        email = "From: alice@example.com\nSubject: News\n\nClick here to unsubscribe from this newsletter."
        assert _classify(email) == "archive_now"

    def test_body_monitor_keyword(self):
        email = "From: alice@example.com\nSubject: Update\n\nFYI, the deployment went smoothly."
        assert _classify(email) == "monitor"

    def test_body_borderline_keyword(self):
        email = "From: alice@example.com\nSubject: Quick question\n\nWhat do you think about the proposal?"
        assert _classify(email) == "borderline"

    # -- Symbiont fallback --

    def test_genuinely_ambiguous_returns_empty(self):
        email = "From: alice@example.com\nSubject: Hello\n\nJust checking in."
        assert _classify(email) == ""

    # -- Ordering: sender beats subject beats body --

    def test_sender_beats_action_subject(self):
        # Even with [Action Required] in subject, automated sender wins
        email = "From: noreply@amazonses.com\nSubject: [Action Required] Verify email\n\nClick to verify."
        assert _classify(email) == "archive_now"

    def test_sender_beats_body_action_keyword(self):
        # Automated sender wins even when body has action keywords
        email = (
            "From: no-reply@mailchimp.com\nSubject: Alert\n\nUrgent: your account needs attention."
        )
        assert _classify(email) == "archive_now"

    def test_subject_beats_body_keyword(self):
        # [Action Required] subject wins over body monitor keywords
        email = "From: alice@example.com\nSubject: [Action Required] Review doc\n\nFYI this needs attention."
        assert _classify(email) == "action_required"
