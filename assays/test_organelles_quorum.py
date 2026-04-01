from __future__ import annotations

"""Tests for metabolon.organelles.quorum — multi-model deliberation engine."""

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.quorum import (
    COUNCIL_DIR,
    CRITIC_MODEL,
    JUDGE_MODEL,
    PANEL_COUNCIL,
    PANEL_DEEP,
    PANEL_QUICK,
    PANEL_REDTEAM,
    Contribution,
    Deliberation,
    _blind_prompt,
    _cross_examine_prompt,
    _debate_prompt,
    _debate_round2_prompt,
    _judge_prompt,
    _mode_council,
    _mode_deep,
    _mode_quick,
    _mode_redteam,
    _parse_judge,
    _redteam_attack_prompt,
    _redteam_defend_prompt,
    deliberate,
    main,
)


# ── fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def sample_contributions():
    return [
        Contribution(model="gemini", content="Use Kafka for durability.", phase="blind"),
        Contribution(model="claude", content="Redis Streams is simpler.", phase="blind"),
        Contribution(model="goose", content="Depends on scale.", phase="blind"),
    ]


@pytest.fixture
def judge_output():
    return textwrap.dedent("""\
        [DECISION] Use Redis Streams for simplicity unless you need Kafka-level durability.
        [REASONING]
        - Simplicity wins for most use cases
        - Kafka is overkill for small teams
        [DISSENT] If you need exactly-once semantics, Kafka is mandatory.
        [DISSENT] Redis persistence is not as robust.
    """)


# ── Contribution dataclass ────────────────────────────────────────


def test_contribution_fields():
    c = Contribution(model="gemini", content="hello", phase="blind")
    assert c.model == "gemini"
    assert c.content == "hello"
    assert c.phase == "blind"


# ── Deliberation dataclass ────────────────────────────────────────


def test_deliberation_defaults():
    d = Deliberation(question="Q?", mode="quick")
    assert d.contributions == []
    assert d.decision == ""
    assert d.dissents == []
    assert d.elapsed_s == 0.0
    assert d.persona == ""


def test_deliberation_summary_no_dissents():
    d = Deliberation(question="Q?", mode="quick", decision="Yes")
    s = d.summary()
    assert "## Decision" in s
    assert "Yes" in s
    assert "Dissents" not in s
    assert "Mode: quick" in s


def test_deliberation_summary_with_dissents():
    d = Deliberation(question="Q?", mode="council", decision="No", dissents=["But maybe?"])
    s = d.summary()
    assert "## Dissents" in s
    assert "- But maybe?" in s


def test_deliberation_summary_elapsed():
    d = Deliberation(question="Q?", mode="quick", elapsed_s=12.3)
    assert "12.3s" in d.summary()


def test_deliberation_transcript_basic():
    d = Deliberation(question="What?", mode="quick", decision="Answer")
    d.contributions.append(Contribution(model="gemini", content="Blind take", phase="blind"))
    t = d.transcript()
    assert "# Quorum: What?" in t
    assert "[blind] gemini" in t
    assert "Blind take" in t
    assert "## Decision" in t


def test_deliberation_transcript_with_persona():
    d = Deliberation(question="Q?", mode="quick", persona="startup CTO", decision="Go")
    t = d.transcript()
    assert "_Persona: startup CTO_" in t


def test_deliberation_transcript_without_persona():
    d = Deliberation(question="Q?", mode="quick", decision="Go")
    t = d.transcript()
    assert "Persona" not in t


def test_deliberation_save(tmp_path):
    d = Deliberation(question="Save test?", mode="quick", decision="Saved!")
    d.persona = "tester"
    d.contributions.append(Contribution(model="m1", content="c1", phase="blind"))

    out = d.save(path=tmp_path / "test-save.md")
    assert out.exists()
    text = out.read_text()
    assert "# Quorum: Save test?" in text
    assert "Saved!" in text


def test_deliberation_save_creates_council_dir(tmp_path, monkeypatch):
    """save() with no path arg creates COUNCIL_DIR and writes there."""
    fake_dir = tmp_path / "councils"
    monkeypatch.setattr("metabolon.organelles.quorum.COUNCIL_DIR", fake_dir)
    d = Deliberation(question="Q?", mode="quick", decision="D")
    out = d.save()
    assert fake_dir.exists()
    assert out.parent == fake_dir
    assert "D" in out.read_text()


def test_deliberation_save_default_path_uses_council_dir(tmp_path):
    d = Deliberation(question="auto path test?", mode="quick", decision="D")
    with patch.object(Deliberation, "save", wraps=d.save) as spy:
        # Just call save with no args — it writes to COUNCIL_DIR
        out = d.save()
        assert out.parent == COUNCIL_DIR
        assert out.exists()


# ── Prompt templates ──────────────────────────────────────────────


def test_blind_prompt_basic():
    p = _blind_prompt("What is 2+2?")
    assert "What is 2+2?" in p
    assert "Context about the questioner" not in p


def test_blind_prompt_with_persona():
    p = _blind_prompt("What?", persona="engineer")
    assert "Context about the questioner: engineer" in p


def test_debate_prompt_excludes_self(sample_contributions):
    p = _debate_prompt("Q?", sample_contributions, "gemini")
    assert "gemini" not in p.replace("**gemini**:", "")
    # claude and goose should appear
    assert "claude" in p
    assert "goose" in p


def test_debate_prompt_includes_question():
    c = [Contribution(model="a", content="ans", phase="blind")]
    p = _debate_prompt("my question?", c, "b")
    assert "my question?" in p


def test_debate_round2_prompt_excludes_self(sample_contributions):
    p = _debate_round2_prompt("Q?", sample_contributions, "claude")
    assert "claude" not in p.replace("**claude**:", "")
    assert "gemini" in p


def test_judge_prompt_basic(sample_contributions):
    p = _judge_prompt("Q?", sample_contributions)
    assert "[DECISION]" in p
    assert "[REASONING]" in p
    assert "[DISSENT]" in p
    assert "gemini" in p
    assert "claude" in p


def test_judge_prompt_with_persona(sample_contributions):
    p = _judge_prompt("Q?", sample_contributions, persona="startup")
    assert "questioner's context: startup" in p


def test_redteam_attack_prompt():
    p = _redteam_attack_prompt("Q?", "Use microservices")
    assert "red team" in p.lower()
    assert "Use microservices" in p
    assert "Q?" in p


def test_redteam_defend_prompt():
    attacks = [
        Contribution(model="a1", content="too complex", phase="attack"),
        Contribution(model="a2", content="overkill", phase="attack"),
    ]
    p = _redteam_defend_prompt("Q?", "Use monolith", attacks)
    assert "too complex" in p
    assert "overkill" in p
    assert "Use monolith" in p


def test_cross_examine_prompt_excludes_self(sample_contributions):
    p = _cross_examine_prompt("Q?", sample_contributions, "gemini")
    assert "gemini" not in p.replace("**gemini**", "")
    assert "claude" in p


# ── _parse_judge ──────────────────────────────────────────────────


def test_parse_judge_full(judge_output):
    decision, dissents = _parse_judge(judge_output)
    assert "Redis Streams" in decision
    assert len(dissents) == 2
    assert "exactly-once" in dissents[0]
    assert "robust" in dissents[1]


def test_parse_judge_no_dissent():
    text = "[DECISION] Use Python.\n[REASONING]\n- Easy\n"
    decision, dissents = _parse_judge(text)
    assert decision == "Use Python."
    assert dissents == []


def test_parse_judge_dissent_none_values():
    text = "[DECISION] Go.\n[DISSENT] none\n[DISSENT] N/A\n[DISSENT] None noted\n"
    decision, dissents = _parse_judge(text)
    assert decision == "Go."
    assert dissents == []


def test_parse_judge_no_decision_fallback():
    text = "First line answer\nMore detail here\n"
    decision, dissents = _parse_judge(text)
    assert decision == "First line answer"


def test_parse_judge_empty_string():
    decision, dissents = _parse_judge("")
    assert decision == ""
    assert dissents == []


def test_parse_judge_multiple_decisions_last_wins():
    text = "[DECISION] First\n[DECISION] Second\n"
    decision, dissents = _parse_judge(text)
    assert decision == "Second"


# ── _mode_quick ───────────────────────────────────────────────────


def test_mode_quick(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.transduce") as t:
        pt.return_value = [("gemini", "ans1"), ("claude", "ans2")]
        t.return_value = "[DECISION] Use Redis.\n[REASONING]\n- Simple\n"

        delib = _mode_quick("Q?", ["gemini", "claude"], "", 60)

        assert delib.mode == "quick"
        assert len(delib.contributions) == 3  # 2 blind + 1 judge
        assert delib.contributions[0].phase == "blind"
        assert delib.contributions[2].phase == "judge"
        assert delib.decision == "Use Redis."
        pt.assert_called_once()
        t.assert_called_once()


# ── _mode_council ─────────────────────────────────────────────────


def test_mode_council(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.parallel_transduce_multi") as ptm, \
         patch("metabolon.organelles.quorum.transduce") as t:

        pt.return_value = [("gemini", "blind1"), ("claude", "blind2")]
        ptm.side_effect = [
            [("gemini", "debate1"), ("claude", "debate2")],  # round 1
            [("gemini", "debate_r2_1"), ("claude", "debate_r2_2")],  # round 2
        ]
        t.side_effect = [
            "[DECISION] Council says yes.\n",  # judge
            "Critic says no!",  # critic
        ]

        delib = _mode_council("Q?", ["gemini", "claude"], "", 60)

        assert delib.mode == "council"
        phases = [c.phase for c in delib.contributions]
        assert "blind" in phases
        assert "debate" in phases
        assert "debate-2" in phases
        assert "judge" in phases
        assert "critic" in phases
        assert delib.decision == "Council says yes."


def test_mode_council_critic_failure_ok(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.parallel_transduce_multi") as ptm, \
         patch("metabolon.organelles.quorum.transduce") as t:

        pt.return_value = [("gemini", "b1")]
        ptm.side_effect = [
            [("gemini", "d1")],
            [("gemini", "d2")],
        ]
        t.side_effect = [
            "[DECISION] Done.\n",  # judge
            RuntimeError("critic failed"),  # critic
        ]

        delib = _mode_council("Q?", ["gemini"], "", 60)
        assert delib.decision == "Done."
        # Critic phase should be silently skipped
        critic_contribs = [c for c in delib.contributions if c.phase == "critic"]
        assert len(critic_contribs) == 0


# ── _mode_redteam ─────────────────────────────────────────────────


def test_mode_redteam(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.transduce") as t:

        pt.return_value = [("claude", "attack1"), ("goose", "attack2")]
        t.side_effect = [
            "Initial position: use Go.",  # blind
            "Defending: Go is great!",  # defend
            "[DECISION] Use Go.\n[DISSENT] Rust is safer.\n",  # judge
        ]

        delib = _mode_redteam("Lang?", ["gemini", "claude", "goose"], "", 60)

        assert delib.mode == "redteam"
        phases = [c.phase for c in delib.contributions]
        assert "blind" in phases
        assert "attack" in phases
        assert "defend" in phases
        assert "judge" in phases
        assert len(delib.dissents) == 1
        assert "Rust" in delib.dissents[0]


# ── _mode_deep ────────────────────────────────────────────────────


def test_mode_deep(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.parallel_transduce_multi") as ptm, \
         patch("metabolon.organelles.quorum.transduce") as t:

        pt.return_value = [("gemini", "b1"), ("claude", "b2")]
        ptm.side_effect = [
            [("gemini", "deb1"), ("claude", "deb2")],  # debate round 1
            [("gemini", "deb2_1"), ("claude", "deb2_2")],  # debate round 2
            [("gemini", "cross1"), ("claude", "cross2")],  # cross-examine
        ]
        t.side_effect = [
            "[DECISION] Deep answer.\n",  # judge
            "Critic remark",  # critic
        ]

        delib = _mode_deep("Deep Q?", ["gemini", "claude"], "", 60)

        assert delib.mode == "deep"
        phases = [c.phase for c in delib.contributions]
        assert phases.count("blind") == 2
        assert phases.count("debate") == 2
        assert phases.count("debate-2") == 2
        assert phases.count("cross-examine") == 2
        assert phases.count("judge") == 1
        assert phases.count("critic") == 1
        assert delib.decision == "Deep answer."


def test_mode_deep_critic_failure_ok(mock_transduce):
    with patch("metabolon.organelles.quorum.parallel_transduce") as pt, \
         patch("metabolon.organelles.quorum.parallel_transduce_multi") as ptm, \
         patch("metabolon.organelles.quorum.transduce") as t:

        pt.return_value = [("gemini", "b1")]
        ptm.side_effect = [
            [("gemini", "d1")],
            [("gemini", "d2")],
            [("gemini", "cx1")],
        ]
        t.side_effect = [
            "[DECISION] Yes.\n",
            RuntimeError("critic down"),
        ]

        delib = _mode_deep("Q?", ["gemini"], "", 60)
        assert delib.decision == "Yes."
        assert not any(c.phase == "critic" for c in delib.contributions)


# ── deliberate() public API ───────────────────────────────────────


def test_deliberate_invalid_mode():
    with pytest.raises(ValueError, match="Unknown mode"):
        deliberate("Q?", mode="nonexistent")


def test_deliberate_quick_dispatch():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [100.0, 115.0]
        mq.return_value = Deliberation(question="Q?", mode="quick")

        result = deliberate("Q?", mode="quick", save=False)
        assert result.elapsed_s == 15.0
        mq.assert_called_once_with("Q?", PANEL_QUICK, "", 180)


def test_deliberate_custom_panel():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [0.0, 1.0]
        mq.return_value = Deliberation(question="Q?", mode="quick")

        deliberate("Q?", panel=["custom1", "custom2"], save=False)
        mq.assert_called_once_with("Q?", ["custom1", "custom2"], "", 180)


def test_deliberate_save_true():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [0.0, 1.0]
        d = Deliberation(question="Q?", mode="quick")
        mq.return_value = d

        with patch.object(d, "save") as save_mock:
            deliberate("Q?", mode="quick", save=True)
            save_mock.assert_called_once()


def test_deliberate_save_false():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [0.0, 1.0]
        d = Deliberation(question="Q?", mode="quick")
        mq.return_value = d

        with patch.object(d, "save") as save_mock:
            deliberate("Q?", mode="quick", save=False)
            save_mock.assert_not_called()


def test_deliberate_all_modes_dispatch():
    """All four modes should dispatch without error."""
    for mode_name, panel in [("quick", PANEL_QUICK), ("council", PANEL_COUNCIL),
                              ("redteam", PANEL_REDTEAM), ("deep", PANEL_DEEP)]:
        with patch(f"metabolon.organelles.quorum._mode_{mode_name}") as mm, \
             patch("metabolon.organelles.quorum.time") as mock_time:
            mock_time.time.side_effect = [0.0, 1.0]
            mm.return_value = Deliberation(question="Q?", mode=mode_name)

            result = deliberate("Q?", mode=mode_name, save=False)
            assert result.mode == mode_name


def test_deliberate_passes_persona():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [0.0, 1.0]
        mq.return_value = Deliberation(question="Q?", mode="quick")

        deliberate("Q?", persona="data engineer", save=False)
        mq.assert_called_once_with("Q?", PANEL_QUICK, "data engineer", 180)


def test_deliberate_custom_timeout():
    with patch("metabolon.organelles.quorum._mode_quick") as mq, \
         patch("metabolon.organelles.quorum.time") as mock_time:
        mock_time.time.side_effect = [0.0, 1.0]
        mq.return_value = Deliberation(question="Q?", mode="quick")

        deliberate("Q?", timeout=300, save=False)
        mq.assert_called_once_with("Q?", PANEL_QUICK, "", 300)


# ── CLI main() ────────────────────────────────────────────────────


def test_main_text_output(capsys):
    d = Deliberation(question="Q?", mode="quick", decision="Yes")
    d.elapsed_s = 1.0
    with patch("metabolon.organelles.quorum.deliberate", return_value=d):
        with pytest.raises(SystemExit) if False else _dummy_context():
            pass
    # Use subprocess-style invocation via argparse
    import sys
    old_argv = sys.argv
    sys.argv = ["quorum", "Test question", "--mode", "quick", "--no-save"]
    try:
        with patch("metabolon.organelles.quorum.deliberate", return_value=d):
            main()
        captured = capsys.readouterr()
        assert "Yes" in captured.out
    finally:
        sys.argv = old_argv


def test_main_json_output(capsys):
    d = Deliberation(question="Q?", mode="quick", decision="JSON answer")
    d.elapsed_s = 2.0
    d.contributions.append(Contribution(model="gemini", content="hello", phase="blind"))
    import sys
    old_argv = sys.argv
    sys.argv = ["quorum", "Q?", "--mode", "quick", "--no-save", "--json"]
    try:
        with patch("metabolon.organelles.quorum.deliberate", return_value=d):
            main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["decision"] == "JSON answer"
        assert data["mode"] == "quick"
        assert len(data["contributions"]) == 1
        assert data["contributions"][0]["model"] == "gemini"
    finally:
        sys.argv = old_argv


def test_main_passes_args():
    d = Deliberation(question="Q?", mode="council", decision="D")
    import sys
    old_argv = sys.argv
    sys.argv = ["quorum", "My Q", "--mode", "council", "--persona", "CTO", "--timeout", "60", "--no-save"]
    try:
        with patch("metabolon.organelles.quorum.deliberate", return_value=d) as mock_del:
            main()
        mock_del.assert_called_once_with(
            "My Q", mode="council", persona="CTO", timeout=60, save=False
        )
    finally:
        sys.argv = old_argv


# ── Panel constants ───────────────────────────────────────────────


def test_panels_are_non_empty():
    assert len(PANEL_QUICK) >= 2
    assert len(PANEL_COUNCIL) >= 2
    assert len(PANEL_REDTEAM) >= 2
    assert len(PANEL_DEEP) >= 2


def test_judge_critic_models_defined():
    assert isinstance(JUDGE_MODEL, str) and len(JUDGE_MODEL) > 0
    assert isinstance(CRITIC_MODEL, str) and len(CRITIC_MODEL) > 0


# ── helpers ───────────────────────────────────────────────────────

# No-op context manager for cleaner conditional logic
from contextlib import nullcontext as _dummy_context


@pytest.fixture(autouse=True)
def mock_transduce():
    """Marker fixture — actual patching done per-test for clarity."""
    yield
