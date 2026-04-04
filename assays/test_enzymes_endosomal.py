from __future__ import annotations

"""Tests for metabolon.enzymes.endosomal — Gmail email triage enzyme.

All external calls (invoke_organelle, synthesize, organelle classify)
are mocked so tests run without Gmail or LLM access.
"""

import pytest

import metabolon.enzymes.endosomal as mod
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_cytosol(monkeypatch):
    """Mock gmail organelle and synthesize for every test."""
    monkeypatch.setattr(mod, "synthesize", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "search", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "get_thread", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "archive", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "mark_read", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "create_label", lambda *a, **kw: "")
    monkeypatch.setattr(mod.gmail, "send_email", lambda *a, **kw: "")
    monkeypatch.setattr(mod.endosomal_organelle, "classify", lambda *a, **kw: "action_required")


@pytest.fixture()
def fn():
    """Return the endosomal function with generic name for brevity."""
    return mod.endosomal


# ---------------------------------------------------------------------------
# Validation / missing-arg tests
# ---------------------------------------------------------------------------


class TestValidation:
    """Each action validates its required parameters."""

    def test_search_requires_query(self, fn):
        res = fn(action="search")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "query" in res.message

    def test_thread_requires_thread_id(self, fn):
        res = fn(action="thread")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "thread_id" in res.message

    def test_categorize_requires_email_text(self, fn):
        res = fn(action="categorize")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "email_text" in res.message

    def test_archive_requires_message_ids(self, fn):
        res = fn(action="archive")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "message_ids" in res.message

    def test_archive_empty_list_fails(self, fn):
        res = fn(action="archive", message_ids=[])
        assert isinstance(res, EffectorResult)
        assert res.success is False

    def test_mark_read_requires_message_ids(self, fn):
        res = fn(action="mark_read")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "message_ids" in res.message

    def test_label_requires_name(self, fn):
        res = fn(action="label")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "name" in res.message

    def test_send_new_email_requires_to_subject_body(self, fn):
        res = fn(action="send", to="a@b.com", subject="hi")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "to, subject, and body" in res.message

    def test_send_reply_only_needs_reply_to(self, fn):
        """A reply only requires reply_to_message_id; no to/subject/body needed."""
        res = fn(action="send", reply_to_message_id="msg123")
        assert isinstance(res, EffectorResult)
        assert res.success is True

    def test_filter_requires_criteria(self, fn):
        res = fn(action="filter")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "from_sender" in res.message or "subject_pattern" in res.message

    def test_filter_requires_action(self, fn):
        res = fn(action="filter", from_sender="spam@x.com")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "add_label" in res.message or "action" in res.message.lower()

    def test_unknown_action(self, fn):
        res = fn(action="explode")
        assert isinstance(res, EffectorResult)
        assert res.success is False
        assert "Unknown action" in res.message

    def test_action_case_insensitive(self, fn):
        """Action matching should be case-insensitive and strip whitespace."""
        res = fn(action="  SEARCH  ", query="inbox")
        assert isinstance(res, mod.EndosomalResult)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_returns_endosomal_result(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "msg1\nmsg2")
        res = fn(action="search", query="from:boss")
        assert isinstance(res, mod.EndosomalResult)
        assert "msg1" in res.output

    def test_search_passes_query_to_invoke(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "")[1],
        )
        fn(action="search", query="is:unread")
        assert calls[0] == ["gmail", "search", "is:unread", "--plain"]


# ---------------------------------------------------------------------------
# thread
# ---------------------------------------------------------------------------


class TestThread:
    def test_thread_returns_content(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "thread-body")
        res = fn(action="thread", thread_id="t123")
        assert isinstance(res, mod.EndosomalResult)
        assert res.output == "thread-body"

    def test_thread_passes_thread_id(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "")[1],
        )
        fn(action="thread", thread_id="t456")
        assert calls[0] == ["gmail", "thread", "get", "t456", "--full"]


# ---------------------------------------------------------------------------
# categorize
# ---------------------------------------------------------------------------


class TestCategorize:
    def test_categorize_uses_deterministic_classify(self, fn, monkeypatch):
        """If the organelle classify() returns a category, use it directly."""
        monkeypatch.setattr(mod.endosomal_organelle, "classify", lambda text: "action_required")
        res = fn(action="categorize", email_text="urgent please review")
        assert isinstance(res, mod.EndosomalResult)
        assert res.output == "action_required"

    def test_categorize_falls_back_to_synthesize(self, fn, monkeypatch):
        """If classify() returns empty, fall back to LLM via synthesize."""
        monkeypatch.setattr(mod.endosomal_organelle, "classify", lambda text: "")
        monkeypatch.setattr(mod, "synthesize", lambda prompt, **kw: "  action_required  ")
        res = fn(action="categorize", email_text="some ambiguous email")
        assert isinstance(res, mod.EndosomalResult)
        assert res.output == "action_required"

    def test_categorize_unclassified_from_synthesize(self, fn, monkeypatch):
        """If synthesize returns something not in CATEGORIES, mark unclassified."""
        monkeypatch.setattr(mod.endosomal_organelle, "classify", lambda text: "")
        monkeypatch.setattr(mod, "synthesize", lambda prompt, **kw: "gibberish_category")
        res = fn(action="categorize", email_text="some email")
        assert isinstance(res, mod.EndosomalResult)
        assert "Unclassified" in res.output

    def test_categorize_normalizes_synthesize_output(self, fn, monkeypatch):
        """synthesize output is stripped, lowered, dashes→underscores."""
        monkeypatch.setattr(mod.endosomal_organelle, "classify", lambda text: "")
        monkeypatch.setattr(mod, "synthesize", lambda prompt, **kw: "  ACTION-REQUIRED \n")
        res = fn(action="categorize", email_text="email text")
        assert res.output == "action_required"


# ---------------------------------------------------------------------------
# archive
# ---------------------------------------------------------------------------


class TestArchive:
    def test_archive_success(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "Archived 2 messages.")
        res = fn(action="archive", message_ids=["m1", "m2"])
        assert isinstance(res, EffectorResult)
        assert res.success is True
        assert "Archived 2" in res.message

    def test_archive_empty_invoke_result(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "")
        res = fn(action="archive", message_ids=["m1"])
        assert res.success is True
        assert "Archived 1" in res.message

    def test_archive_passes_force_flag(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "")[1],
        )
        fn(action="archive", message_ids=["id1", "id2"])
        assert calls[0] == ["gmail", "archive", "--force", "id1", "id2"]


# ---------------------------------------------------------------------------
# mark_read
# ---------------------------------------------------------------------------


class TestMarkRead:
    def test_mark_read_success(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "Marked 3 read.")
        res = fn(action="mark_read", message_ids=["m1", "m2", "m3"])
        assert isinstance(res, EffectorResult)
        assert res.success is True

    def test_mark_read_default_message(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "")
        res = fn(action="mark_read", message_ids=["m1"])
        assert "Marked 1" in res.message


# ---------------------------------------------------------------------------
# label
# ---------------------------------------------------------------------------


class TestLabel:
    def test_label_create(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "Created: ProjectX")
        res = fn(action="label", name="ProjectX")
        assert isinstance(res, EffectorResult)
        assert res.success is True
        assert "ProjectX" in res.message

    def test_label_default_message(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "")
        res = fn(action="label", name="foo")
        assert res.message == "Label created: foo"


# ---------------------------------------------------------------------------
# send
# ---------------------------------------------------------------------------


class TestSend:
    def test_send_new_email(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "sent-ok")[1],
        )
        res = fn(
            action="send",
            to="a@b.com",
            subject="hello",
            body="world",
        )
        assert res.success is True
        assert calls[0] == [
            "gmail",
            "send",
            "--to",
            "a@b.com",
            "--subject",
            "hello",
            "--body",
            "world",
        ]

    def test_send_reply(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "")[1],
        )
        res = fn(action="send", reply_to_message_id="mid42", body="thanks")
        assert res.success is True
        assert "--reply-to-message-id" in calls[0]
        assert "mid42" in calls[0]
        assert "--reply-all" in calls[0]
        assert "--quote" in calls[0]

    def test_send_with_cc_and_attach(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "")[1],
        )
        res = fn(
            action="send",
            to="x@y.com",
            subject="sub",
            body="bod",
            cc="z@y.com",
            attach=["/tmp/file.pdf"],
        )
        assert res.success is True
        assert "--cc" in calls[0]
        assert "z@y.com" in calls[0]
        assert "--attach" in calls[0]
        assert "/tmp/file.pdf" in calls[0]

    def test_send_default_message(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "")
        res = fn(action="send", to="a@b", subject="s", body="b")
        assert res.message == "Email sent."


# ---------------------------------------------------------------------------
# filter
# ---------------------------------------------------------------------------


class TestFilter:
    def test_filter_dry_run(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "preview")[1],
        )
        res = fn(
            action="filter",
            from_sender="noisy@spam.com",
            add_label="bulk",
            dry_run=True,
        )
        assert res.success is True
        assert "[DRY RUN]" in res.message
        assert "--dry-run" in calls[0]

    def test_filter_live(self, fn, monkeypatch):
        calls = []
        monkeypatch.setattr(
            mod,
            "invoke_organelle",
            lambda gog, args, **kw: (calls.append(args), "created")[1],
        )
        res = fn(
            action="filter",
            subject_pattern="newsletter",
            archive=True,
            mark_read=True,
            dry_run=False,
        )
        assert res.success is True
        assert "[DRY RUN]" not in res.message
        assert "--archive" in calls[0]
        assert "--mark-read" in calls[0]
        assert "--dry-run" not in calls[0]

    def test_filter_default_message(self, fn, monkeypatch):
        monkeypatch.setattr(mod, "invoke_organelle", lambda *a, **kw: "")
        res = fn(
            action="filter",
            from_sender="x@y.com",
            add_label="test",
            dry_run=False,
        )
        assert res.success is True
        assert "Filter applied." in res.message
