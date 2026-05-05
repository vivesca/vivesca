"""Assays for named-tool-pushback detector (sub-detector A).

Per spec: synapse-reactive-not-proactive-detector.md §Sub-detector A.
POS fixtures: pushback + named entity → fires.
NEG fixtures: missing pushback or named entity → silent.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

SYNAPSE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "membrane" / "cytoskeleton" / "synapse.py"
)

_spec = importlib.util.spec_from_file_location("synapse", str(SYNAPSE_PATH))
_synapse = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_synapse)

_sense_pushback = _synapse._sense_pushback
_flag_named_antigens = _synapse._flag_named_antigens
mod_named_tool_pushback = _synapse.mod_named_tool_pushback


# ── Pushback signal detection ──────────────────────────────────


class TestSensePushback:
    def test_but_keyword(self):
        assert _sense_pushback("but Hermes Agent and OpenClaw both ship with this")

    def test_really_keyword(self):
        assert _sense_pushback("really? did you check Anthropic's 2026 report?")

    def test_are_you_sure(self):
        assert _sense_pushback("are you sure GMIS is a gate not a system?")

    def test_actually_keyword(self):
        assert _sense_pushback("Actually, that's not right")

    def test_didnt_you(self):
        assert _sense_pushback("didn't you say it was broken?")

    def test_have_you(self):
        assert _sense_pushback("have you tested this?")

    def test_did_you_check(self):
        assert _sense_pushback("did you check the logs?")

    def test_you_said(self):
        assert _sense_pushback("you said it was done yesterday")

    def test_is_it(self):
        assert _sense_pushback("is it really safe?")

    def test_no_pushback_draft(self):
        assert not _sense_pushback("draft an email to Simon")

    def test_no_pushback_opinion(self):
        assert not _sense_pushback("I think Compliance owns it")

    def test_no_pushback_thanks(self):
        assert not _sense_pushback("thanks")


# ── Named antigen detection ────────────────────────────────────


class TestFlagNamedAntigens:
    def test_hermes_agent_openclaw(self):
        tokens = _flag_named_antigens("but Hermes Agent and OpenClaw both ship with this")
        token_set = set(tokens)
        assert "Hermes" in token_set
        assert "Agent" in token_set
        assert "OpenClaw" in token_set

    def test_anthropic(self):
        tokens = _flag_named_antigens("really? did you check Anthropic's 2026 report?")
        assert any("Anthropic" in t for t in tokens)

    def test_gmis(self):
        tokens = _flag_named_antigens("are you sure GMIS is a gate not a system?")
        assert "GMIS" in tokens

    def test_compliance_in_stoplist(self):
        tokens = _flag_named_antigens("I think Compliance owns it")
        assert "Compliance" not in tokens

    def test_weekday_in_stoplist(self):
        tokens = _flag_named_antigens("but Monday we shipped it")
        assert "Monday" not in tokens

    def test_month_in_stoplist(self):
        tokens = _flag_named_antigens("but January showed growth")
        assert "January" not in tokens

    def test_sentence_start_excluded(self):
        tokens = _flag_named_antigens("Simon said this")
        assert "Simon" not in tokens

    def test_mid_sentence_capitalised_detected(self):
        tokens = _flag_named_antigens("but did you ask Simon about this")
        assert "Simon" in tokens

    def test_camelcase_detected(self):
        tokens = _flag_named_antigens("but OpenClaw is great")
        assert "OpenClaw" in tokens


# ── Full detector: POS fixtures ────────────────────────────────


class TestNamedToolPushbackPositive:
    @pytest.mark.parametrize(
        "prompt",
        [
            "but Hermes Agent and OpenClaw both ship with this",
            "really? did you check Anthropic's 2026 report?",
            "are you sure GMIS is a gate not a system?",
        ],
        ids=["hermes_openclaw", "anthropic_report", "gmis_gate"],
    )
    def test_fires_on_pushback_with_named_entity(self, prompt):
        result = mod_named_tool_pushback({"prompt": prompt})
        assert len(result) >= 1
        msg = result[0].lower()
        assert "entity" in msg
        assert "rheotaxis" in msg
        assert "finding_run_empirical_check_on_named_tools_immediately" in msg


# ── Full detector: NEG fixtures ────────────────────────────────


class TestNamedToolPushbackNegative:
    @pytest.mark.parametrize(
        "prompt",
        [
            "draft an email to Simon",
            "I think Compliance owns it",
            "thanks",
        ],
        ids=["draft_email", "compliance_opinion", "thanks"],
    )
    def test_does_not_fire(self, prompt):
        result = mod_named_tool_pushback({"prompt": prompt})
        assert result == []

    def test_empty_prompt(self):
        assert mod_named_tool_pushback({"prompt": ""}) == []

    def test_missing_prompt_key(self):
        assert mod_named_tool_pushback({}) == []
