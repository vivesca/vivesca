from __future__ import annotations

"""Tests for metabolon.organelles.quorum — multi-model deliberation engine."""

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from metabolon.organelles.quorum import (
    Contribution,
    Deliberation,
    PANEL_QUICK,
    PANEL_COUNCIL,
    PANEL_REDTEAM,
    PANEL_DEEP,
    JUDGE_MODEL,
    CRITIC_MODEL,
    _blind_prompt,
    _debate_prompt,
    _debate_round2_prompt,
    _judge_prompt,
    _redteam_attack_prompt,
    _redteam_defend_prompt,
    _cross_examine_prompt,
    _parse_judge,
    _mode_quick,
    _mode_council,
    _mode_redteam,
    _mode_deep,
    deliberate,
)


# ── Contribution dataclass ───────────────────────────────────────────


def test_contribution_fields():
    c = Contribution(model="gemini", content="hello", phase="blind")
    assert c.model == "gemini"
    assert c.content == "hello"
    assert c.phase == "blind"


# ── Deliberation dataclass ───────────────────────────────────────────


def test_deliberation_defaults():
    d = Deliberation(question="Q?", mode="quick")
    assert d.contributions == []
    assert d.decision == ""
    assert d.dissents == []
    assert d.elapsed_s == 0.0
    assert d.persona == ""


def test_deliberation_summary_no_dissents():
    d = Deliberation(question="Q?", mode="quick", decision="Do X", elapsed_s=3.2)
    s = d.summary()
    assert "## Decision" in s
    assert "Do X" in s
    assert "Dissents" not in s
    assert "_Mode: quick | 3.2s_" in s


def test_deliberation_summary_with_dissents():
    d = Deliberation(question="Q?", mode="council", decision="Do Y",
                     dissents=["But Z!", "Also W"], elapsed_s=5.0)
    s = d.summary()
    assert "## Dissents" in s
    assert "- But Z!" in s
    assert "- Also W" in s


def test_deliberation_transcript():
    d = Deliberation(question="What?", mode="quick", persona="engineer",
                     contributions=[
                         Contribution(model="gemini", content="ans1", phase="blind"),
                         Contribution(model="claude", content="ans2", phase="judge"),
                     ],
                     decision="final")
    t = d.transcript()
    assert "# Quorum: What?" in t
    assert "_Persona: engineer_" in t
    assert "## [blind] gemini" in t
    assert "ans1" in t
    assert "## [judge] claude" in t
    assert "ans2" in t
    assert "---" in t


def test_deliberation_transcript_no_persona():
    d = Deliberation(question="Q?", mode="quick")
    t = d.transcript()
    assert "Persona" not in t


def test_deliberation_save(tmp_path):
    d = Deliberation(question="Save me please?", mode="quick", decision="Done")
    out = d.save(path=tmp_path / "test.md")
    assert out.exists()
    content = out.read_text()
    assert "Done" in content
    assert "Save me please?" in content


def test_deliberation_save_slug_sanitization(tmp_path):
    d = Deliberation(question="a/b c!d@e", mode="quick", decision="ok")
    out = d.save(path=tmp_path / "slug.md")
    assert out.exists()


# ── _parse_judge ─────────────────────────────────────────────────────


def test_parse_judge_extracts_decision_and_dissent():
    text = "[DECISION] Use Redis\n[REASONING] blah\n[DISSENT] Kafka is better"
    decision, dissents = _parse_judge(text)
    assert decision == "Use Redis"
    assert dissents == ["Kafka is better"]


def test_parse_judge_multiple_dissents():
    text = "[DECISION] Go\n[DISSENT] Rust\n[DISSENT] Python"
    decision, dissents = _parse_judge(text)
    assert decision == "Go"
    assert dissents == ["Rust", "Python"]


def test_parse_judge_no_dissent():
    text = "[DECISION] Just do it\n[REASONING] Reasons"
    decision, dissents = _parse_judge(text)
    assert decision == "Just do it"
    assert dissents == []


def test_parse_judge_dissent_none_na_filtered():
    text = "[DECISION] Yes\n[DISSENT] None\n[DISSENT] N/A\n[DISSENT] None noted"
    decision, dissents = _parse_judge(text)
    assert dissents == []


def test_parse_judge_fallback_first_line():
    text = "Something without brackets\nMore text"
    decision, dissents = _parse_judge(text)
    assert decision == "Something without brackets"
    assert dissents == []


def test_parse_judge_empty_string():
    decision, dissents = _parse_judge("")
    assert decision == ""
    assert dissents == []


# ── Prompt templates ─────────────────────────────────────────────────


def test_blind_prompt_basic():
    p = _blind_prompt("What is X?")
    assert "What is X?" in p
    assert "Context about the questioner" not in p


def test_blind_prompt_with_persona():
    p = _blind_prompt("What is X?", persona="senior dev")
    assert "Context about the questioner: senior dev" in p


def test_debate_prompt_excludes_self():
    contribs = [
        Contribution(model="gemini", content="g-answer", phase="blind"),
        Contribution(model="claude", content="c-answer", phase="blind"),
    ]
    p = _debate_prompt("Q?", contribs, "gemini")
    assert "claude" in p
    assert "c-answer" in p
    # gemini should NOT appear as "other"
    assert "**gemini**" not in p


def test_debate_round2_prompt():
    contribs = [
        Contribution(model="gemini", content="r1-g", phase="debate"),
        Contribution(model="claude", content="r1-c", phase="debate"),
    ]
    p = _debate_round2_prompt("Q?", contribs, "claude")
    assert "round 2" in p.lower()
    assert "r1-g" in p
    assert "gemini" in p


def test_judge_prompt_includes_all_contributions():
    contribs = [
        Contribution(model="a", content="x", phase="blind"),
        Contribution(model="b", content="y", phase="debate"),
    ]
    p = _judge_prompt("Q?", contribs)
    assert "**a** [blind]" in p
    assert "**b** [debate]" in p
    assert "[DECISION]" in p
    assert "[REASONING]" in p
    assert "[DISSENT]" in p


def test_judge_prompt_with_persona():
    p = _judge_prompt("Q?", [], persona="PM")
    assert "questioner's context: PM" in p


def test_redteam_attack_prompt():
    p = _redteam_attack_prompt("Q?", "position text")
    assert "red team" in p.lower()
    assert "Q?" in p
    assert "position text" in p


def test_redteam_defend_prompt():
    attacks = [Contribution(model="atk1", content="bad idea", phase="attack")]
    p = _redteam_defend_prompt("Q?", "position", attacks)
    assert "under attack" in p.lower()
    assert "bad idea" in p


def test_cross_examine_prompt():
    contribs = [
        Contribution(model="a", content="weak arg", phase="debate"),
        Contribution(model="b", content="strong arg", phase="debate"),
    ]
    p = _cross_examine_prompt("Q?", contribs, "a")
    assert "weakest" in p.lower()
    assert "strong arg" in p
    # model "a" should be excluded
    assert "weak arg" not in p


# ── _mode_quick ──────────────────────────────────────────────────────


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_quick(mock_parallel, mock_transduce):
    mock_parallel.return_value = [("gemini", "ans-g"), ("claude", "ans-c")]
    mock_transduce.return_value = "[DECISION] Use X\n[DISSENT] Use Y"

    d = _mode_quick("Q?", ["gemini", "claude"], "", 60)

    assert d.mode == "quick"
    assert d.question == "Q?"
    # 2 blind + 1 judge
    assert len(d.contributions) == 3
    phases = [c.phase for c in d.contributions]
    assert phases.count("blind") == 2
    assert "judge" in phases
    assert d.decision == "Use X"
    assert d.dissents == ["Use Y"]
    mock_parallel.assert_called_once()
    mock_transduce.assert_called_once()


# ── _mode_council ────────────────────────────────────────────────────


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce_multi")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_council(mock_parallel, mock_parallel_multi, mock_transduce):
    # Phase 1: blind
    mock_parallel.return_value = [("gemini", "blind-g"), ("claude", "blind-c")]
    # Phase 2: debate round 1, round 2 (two parallel_transduce_multi calls)
    mock_parallel_multi.side_effect = [
        [("gemini", "debate1-g"), ("claude", "debate1-c")],
        [("gemini", "debate2-g"), ("claude", "debate2-c")],
    ]
    # Phase 3: judge, Phase 4: critic (two transduce calls)
    mock_transduce.side_effect = [
        "[DECISION] Council says yes",
        "Critic says judge missed Z",
    ]

    d = _mode_council("Q?", ["gemini", "claude"], "", 60)

    assert d.mode == "council"
    # blind×2 + debate×2 + debate-2×2 + judge + critic = 8
    phases = [c.phase for c in d.contributions]
    assert phases.count("blind") == 2
    assert phases.count("debate") == 2
    assert phases.count("debate-2") == 2
    assert "judge" in phases
    assert "critic" in phases
    assert d.decision == "Council says yes"


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce_multi")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_council_critic_failure_graceful(mock_parallel, mock_parallel_multi, mock_transduce):
    mock_parallel.return_value = [("gemini", "b")]
    mock_parallel_multi.side_effect = [
        [("gemini", "d1")],
        [("gemini", "d2")],
    ]
    mock_transduce.side_effect = [
        "[DECISION] OK",
        RuntimeError("API down"),
    ]

    d = _mode_council("Q?", ["gemini"], "", 60)
    phases = [c.phase for c in d.contributions]
    assert "critic" not in phases  # critic should be skipped on exception
    assert d.decision == "OK"


# ── _mode_redteam ────────────────────────────────────────────────────


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_redteam(mock_parallel, mock_transduce):
    # Phase 1: blind (single model via transduce)
    # Phase 2: attack (parallel_transduce)
    # Phase 3: defend (transduce)
    # Phase 4: judge (transduce)
    mock_transduce.side_effect = [
        "initial position",
        "defending position",
        "[DECISION] Survived\n[DISSENT] Barely",
    ]
    mock_parallel.return_value = [("claude", "attack1"), ("goose", "attack2")]

    d = _mode_redteam("Q?", ["gemini", "claude", "goose"], "", 60)

    assert d.mode == "redteam"
    phases = [c.phase for c in d.contributions]
    assert "blind" in phases
    assert phases.count("attack") == 2
    assert "defend" in phases
    assert "judge" in phases
    assert d.decision == "Survived"
    assert d.dissents == ["Barely"]


# ── _mode_deep ───────────────────────────────────────────────────────


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce_multi")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_deep(mock_parallel, mock_parallel_multi, mock_transduce):
    mock_parallel.return_value = [("gemini", "blind-g")]
    mock_parallel_multi.side_effect = [
        [("gemini", "debate1-g")],           # debate round 1
        [("gemini", "debate2-g")],           # debate round 2
        [("gemini", "cross-g")],             # cross-examine
    ]
    mock_transduce.side_effect = [
        "[DECISION] Deep answer",
        "Critic says nah",
    ]

    d = _mode_deep("Q?", ["gemini"], "", 60)

    assert d.mode == "deep"
    phases = [c.phase for c in d.contributions]
    assert "blind" in phases
    assert "debate" in phases
    assert "debate-2" in phases
    assert "cross-examine" in phases
    assert "judge" in phases
    assert "critic" in phases
    assert d.decision == "Deep answer"


@patch("metabolon.organelles.quorum.transduce")
@patch("metabolon.organelles.quorum.parallel_transduce_multi")
@patch("metabolon.organelles.quorum.parallel_transduce")
def test_mode_deep_critic_failure_graceful(mock_parallel, mock_parallel_multi, mock_transduce):
    mock_parallel.return_value = [("gemini", "b")]
    mock_parallel_multi.side_effect = [
        [("gemini", "d1")],
        [("gemini", "d2")],
        [("gemini", "cx")],
    ]
    mock_transduce.side_effect = [
        "[DECISION] OK",
        RuntimeError("timeout"),
    ]

    d = _mode_deep("Q?", ["gemini"], "", 60)
    phases = [c.phase for c in d.contributions]
    assert "critic" not in phases
    assert d.decision == "OK"


# ── deliberate (public API) ─────────────────────────────────────────


@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_quick_dispatches(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick", decision="X")
    result = deliberate("Q?", mode="quick", save=False)
    mock_mode.assert_called_once_with("Q?", PANEL_QUICK, "", 180)
    assert result.decision == "X"


@patch("metabolon.organelles.quorum._mode_council")
def test_deliberate_council_dispatches(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="council", decision="Y")
    result = deliberate("Q?", mode="council", save=False)
    mock_mode.assert_called_once_with("Q?", PANEL_COUNCIL, "", 180)


@patch("metabolon.organelles.quorum._mode_redteam")
def test_deliberate_redteam_dispatches(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="redteam", decision="Z")
    result = deliberate("Q?", mode="redteam", save=False)
    mock_mode.assert_called_once_with("Q?", PANEL_REDTEAM, "", 180)


@patch("metabolon.organelles.quorum._mode_deep")
def test_deliberate_deep_dispatches(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="deep", decision="W")
    result = deliberate("Q?", mode="deep", save=False)
    mock_mode.assert_called_once_with("Q?", PANEL_DEEP, "", 180)


def test_deliberate_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown mode: badmode"):
        deliberate("Q?", mode="badmode")


@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_custom_panel(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick", decision="ok")
    deliberate("Q?", mode="quick", panel=["model-a", "model-b"], save=False)
    mock_mode.assert_called_once_with("Q?", ["model-a", "model-b"], "", 180)


@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_elapsed_s_set(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick")
    result = deliberate("Q?", mode="quick", save=False)
    assert result.elapsed_s >= 0


@patch("metabolon.organelles.quorum.Deliberation.save")
@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_save_called_by_default(mock_mode, mock_save):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick")
    mock_save.return_value = Path("/tmp/fake.md")
    deliberate("Q?", mode="quick", save=True)
    mock_save.assert_called_once()


@patch("metabolon.organelles.quorum.Deliberation.save")
@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_save_skipped_when_false(mock_mode, mock_save):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick")
    deliberate("Q?", mode="quick", save=False)
    mock_save.assert_not_called()


@patch("metabolon.organelles.quorum._mode_quick")
def test_deliberate_passes_persona_and_timeout(mock_mode):
    mock_mode.return_value = Deliberation(question="Q?", mode="quick")
    deliberate("Q?", mode="quick", persona="CTO", timeout=300, save=False)
    mock_mode.assert_called_once_with("Q?", PANEL_QUICK, "CTO", 300)


# ── Panel constants ──────────────────────────────────────────────────


def test_panel_quick_models():
    assert "gemini" in PANEL_QUICK
    assert "claude" in PANEL_QUICK


def test_panel_council_larger_than_quick():
    assert len(PANEL_COUNCIL) > len(PANEL_QUICK)


def test_panel_deep_largest():
    assert len(PANEL_DEEP) >= len(PANEL_COUNCIL)
    assert len(PANEL_DEEP) >= len(PANEL_REDTEAM)


def test_judge_and_critic_models_differ():
    assert JUDGE_MODEL != CRITIC_MODEL
