"""Tests for checkpoint — phantom task dispatch filter."""

from unittest.mock import patch

from metabolon.checkpoint import (
    MAX_TERRY_PER_SYSTOLE,
    _is_phantom,
    _is_study_or_action,
    _phantom_reason,
    is_terry_tag_approved,
    should_suppress,
    sweep_praxis_for_phantoms,
)

# --- should_suppress ---


def test_approve_sourced_automated():
    ok, _reason = should_suppress({"description": "research HKMA circulars", "sourced": True})
    assert ok is True


def test_block_no_description():
    ok, reason = should_suppress({"description": ""})
    assert ok is False
    assert "no description" in reason


def test_block_wrong_category_presence():
    ok, reason = should_suppress({"description": "attend meeting", "category": "Presence"})
    assert ok is False
    assert "wrong category" in reason


def test_block_wrong_category_sharpening():
    ok, reason = should_suppress({"description": "drill flashcards", "category": "Sharpening"})
    assert ok is False
    assert "wrong category" in reason


def test_block_phantom_unsourced():
    ok, reason = should_suppress(
        {
            "description": "submit conference abstract on AI governance",
            "sourced": False,
        }
    )
    assert ok is False
    assert "phantom" in reason.lower()


def test_allow_phantom_when_sourced():
    ok, _reason = should_suppress(
        {
            "description": "submit conference abstract on AI governance",
            "sourced": True,
        }
    )
    assert ok is True


def test_block_linkedin_draft():
    ok, _reason = should_suppress(
        {
            "description": "draft LinkedIn post about consulting career",
            "sourced": False,
        }
    )
    assert ok is False


def test_allow_code_task():
    ok, _reason = should_suppress(
        {
            "description": "generate test file for checkpoint module",
            "sourced": False,
            "category": "Automated",
        }
    )
    assert ok is True


def test_block_non_automated_heuristic_family():
    ok, reason = should_suppress({"description": "plan Theo's birthday party"})
    assert ok is False
    assert "non-Automated" in reason


def test_allow_automated_category_override():
    ok, _reason = should_suppress(
        {
            "description": "plan Theo's birthday party",
            "category": "Automated",
        }
    )
    # Category explicitly set to Automated bypasses non-automated heuristic
    assert ok is True


# --- _is_phantom ---


def test_phantom_conference():
    assert _is_phantom("submit conference abstract") is True


def test_phantom_linkedin():
    assert _is_phantom("write LinkedIn post draft for review") is True


def test_phantom_self_audit():
    assert _is_phantom("audit yourself for compliance") is True


def test_not_phantom_code():
    assert _is_phantom("write pytest for checkpoint module") is False


def test_not_phantom_research():
    assert _is_phantom("research HKMA AI circular") is False


# --- _phantom_reason ---


def test_phantom_reason_returns_pattern():
    reason = _phantom_reason("submit abstract to conference")
    assert "conference" in reason.lower() or "abstract" in reason.lower()


def test_phantom_reason_empty_for_safe():
    reason = _phantom_reason("refactor checkpoint module")
    assert reason == ""


# --- _is_study_or_action ---


def test_study_task():
    assert _is_study_or_action("study HKMA guidelines from memory") is True


def test_physical_action():
    assert _is_study_or_action("go to office to collect router") is True


def test_verify_complete():
    assert _is_study_or_action("verify tests pass and confirm complete") is True


def test_not_study():
    assert _is_study_or_action("review draft consulting memo") is False


# --- is_terry_tag_approved ---


def test_terry_tag_under_cap():
    ok, _reason = is_terry_tag_approved("review draft memo", current_terry_count=0, sourced=True)
    assert ok is True


def test_terry_tag_at_cap():
    ok, reason = is_terry_tag_approved("review memo", current_terry_count=MAX_TERRY_PER_SYSTOLE)
    assert ok is False
    assert "cap reached" in reason


def test_terry_tag_study_blocked():
    ok, reason = is_terry_tag_approved(
        "study HKMA from memory", current_terry_count=0, sourced=True
    )
    assert ok is False
    assert "not a review item" in reason


# --- sweep_praxis_for_phantoms ---


def test_sweep_finds_phantom(tmp_path):
    with patch("metabolon.checkpoint.PHANTOM_TRACKER", tmp_path / "phantoms.json"):
        praxis = "- [ ] agent:terry submit conference abstract\n- [ ] agent:terry review memo\n"
        results = sweep_praxis_for_phantoms(praxis)
        assert len(results) >= 1
        assert any(
            "conference" in r["reason"].lower() or "abstract" in r["reason"].lower()
            for r in results
        )


def test_sweep_ignores_completed():
    praxis = "- [x] agent:terry submit conference abstract (done)\n"
    results = sweep_praxis_for_phantoms(praxis)
    assert len(results) == 0


def test_sweep_ignores_non_terry():
    praxis = "- [ ] fix bug in checkpoint module\n"
    results = sweep_praxis_for_phantoms(praxis)
    assert len(results) == 0
