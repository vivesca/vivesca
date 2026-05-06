"""Tests for sub-detector C: oscillation detector across dendrite + synapse.

Spec: ~/epigenome/chromatin/loci/plans/synapse-reactive-not-proactive-detector.md §C.

dendrite.mod_oscillation_log logs Edit/MultiEdit hash signatures into a session-scoped
JSONL and writes a flag file when 3+ reversals on the same file are detected.
synapse.mod_oscillation_warning consumes the flag at the next UserPromptSubmit and
emits a non-blocking additionalContext warning.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DENDRITE_PATH = ROOT / "membrane" / "cytoskeleton" / "dendrite.py"
SYNAPSE_PATH = ROOT / "membrane" / "cytoskeleton" / "synapse.py"


def _load_module(name: str, source: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, str(source))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dendrite_module(tmp_path, monkeypatch):
    module = _load_module("dendrite_under_test", DENDRITE_PATH)
    monkeypatch.setattr(module, "_OSCILLATION_SESSIONS_DIR", tmp_path)
    return module


@pytest.fixture
def synapse_module(tmp_path, monkeypatch):
    module = _load_module("synapse_under_test", SYNAPSE_PATH)
    monkeypatch.setattr(module, "_OSCILLATION_SESSIONS_DIR", tmp_path)
    return module


def _edit_event(file_path: str, old: str, new: str, session_id: str = "session-test") -> dict:
    return {
        "tool_name": "Edit",
        "session_id": session_id,
        "tool_input": {"file_path": file_path, "old_string": old, "new_string": new},
    }


class TestNormaliseHash:
    def test_smart_quote_folded(self, dendrite_module):
        ascii_hash = dendrite_module._normalise_for_oscillation_hash("don't")
        smart_hash = dendrite_module._normalise_for_oscillation_hash("don’t")
        assert ascii_hash == smart_hash

    def test_case_folded(self, dendrite_module):
        upper = dendrite_module._normalise_for_oscillation_hash("Why Now")
        lower = dendrite_module._normalise_for_oscillation_hash("why now")
        assert upper == lower

    def test_whitespace_collapsed(self, dendrite_module):
        single = dendrite_module._normalise_for_oscillation_hash("why now")
        multi = dendrite_module._normalise_for_oscillation_hash("why    now")
        padded = dendrite_module._normalise_for_oscillation_hash("  why now  ")
        assert single == multi == padded

    def test_distinct_text_distinct_hash(self, dendrite_module):
        a = dendrite_module._normalise_for_oscillation_hash("Why now")
        b = dendrite_module._normalise_for_oscillation_hash("Why centralise")
        assert a != b

    def test_empty_returns_empty(self, dendrite_module):
        assert dendrite_module._normalise_for_oscillation_hash("") == ""


class TestOscillationLogAndFlag:
    def test_three_round_trips_fire(self, dendrite_module, tmp_path):
        target = "/home/vivesca/draft/paper.md"
        # Edit 1: A → B
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why now", "Why centralise"))
        # Edit 2: B → A (reversal #1)
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why centralise", "Why now"))
        # Edit 3: A → C
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why now", "Why scale"))
        # Edit 4: C → A (reversal #2)
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why scale", "Why now"))
        # Edit 5: A → D
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why now", "Why focus"))
        # Edit 6: D → A (reversal #3) → flag should fire
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why focus", "Why now"))

        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        assert flag_path.exists(), "Flag file should exist after 3 reversals"
        assert flag_path.read_text() == str(pathlib.Path(target).expanduser().resolve())

    def test_distinct_edits_no_fire(self, dendrite_module, tmp_path):
        target = "/home/vivesca/draft/paper.md"
        for index in range(5):
            dendrite_module.mod_oscillation_log(
                _edit_event(target, f"Heading {index}", f"Heading {index + 1}")
            )
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        assert not flag_path.exists(), "5 distinct edits should not fire"

    def test_one_reversal_no_fire(self, dendrite_module, tmp_path):
        target = "/home/vivesca/draft/paper.md"
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why now", "Why centralise"))
        dendrite_module.mod_oscillation_log(_edit_event(target, "Why centralise", "Why now"))
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        assert not flag_path.exists(), "Single reversal should not fire"

    def test_session_isolation(self, dendrite_module, tmp_path):
        target = "/home/vivesca/draft/paper.md"
        for old, new in [("A", "B"), ("B", "A"), ("A", "C"), ("C", "A")]:
            dendrite_module.mod_oscillation_log(
                _edit_event(target, old, new, session_id="session-other")
            )
        # session-other has 2 reversals; session-test has 0
        for old, new in [("A", "B"), ("B", "A")]:
            dendrite_module.mod_oscillation_log(
                _edit_event(target, old, new, session_id="session-test")
            )
        flag_test = tmp_path / "session-test-oscillation-warning.flag"
        flag_other = tmp_path / "session-other-oscillation-warning.flag"
        assert not flag_test.exists(), "session-test below threshold"
        assert not flag_other.exists(), "session-other below threshold"

    def test_no_session_id_graceful(self, dendrite_module):
        event = _edit_event("/home/vivesca/draft/paper.md", "A", "B", session_id="")
        # Should not raise
        dendrite_module.mod_oscillation_log(event)

    def test_non_edit_tool_ignored(self, dendrite_module, tmp_path):
        event = {
            "tool_name": "Read",
            "session_id": "session-test",
            "tool_input": {"file_path": "/home/vivesca/draft/paper.md"},
        }
        dendrite_module.mod_oscillation_log(event)
        # No log file should have been created
        log_path = tmp_path / "session-test-edit-log.jsonl"
        assert not log_path.exists()

    def test_path_normalisation_collapses_relative(self, dendrite_module, tmp_path):
        target_a = "/home/vivesca/./draft/paper.md"
        target_b = "/home/vivesca/draft/paper.md"
        dendrite_module.mod_oscillation_log(_edit_event(target_a, "X", "Y"))
        dendrite_module.mod_oscillation_log(_edit_event(target_b, "Y", "X"))
        dendrite_module.mod_oscillation_log(_edit_event(target_a, "X", "Z"))
        dendrite_module.mod_oscillation_log(_edit_event(target_b, "Z", "X"))
        dendrite_module.mod_oscillation_log(_edit_event(target_a, "X", "W"))
        dendrite_module.mod_oscillation_log(_edit_event(target_b, "W", "X"))
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        assert flag_path.exists(), "Reversals across normalised-equivalent paths should aggregate"


class TestOscillationWarning:
    def test_warning_delivered_when_flag_present(self, synapse_module, tmp_path):
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        flag_path.write_text("/home/vivesca/draft/paper.md")
        result = synapse_module.mod_oscillation_warning({"session_id": "session-test"})
        assert len(result) == 1
        message = result[0]
        assert "/home/vivesca/draft/paper.md" in message
        assert "framing-driven oscillation" in message
        assert "feedback_repeated_ask_signals_empirical_test" in message

    def test_flag_consumed_after_warning(self, synapse_module, tmp_path):
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        flag_path.write_text("/home/vivesca/draft/paper.md")
        synapse_module.mod_oscillation_warning({"session_id": "session-test"})
        assert not flag_path.exists(), "Flag must be consumed once warning is delivered"

    def test_no_warning_when_no_flag(self, synapse_module):
        result = synapse_module.mod_oscillation_warning({"session_id": "session-test"})
        assert result == []

    def test_no_warning_when_no_session_id(self, synapse_module):
        result = synapse_module.mod_oscillation_warning({})
        assert result == []

    def test_empty_flag_returns_no_warning(self, synapse_module, tmp_path):
        flag_path = tmp_path / "session-test-oscillation-warning.flag"
        flag_path.write_text("")
        result = synapse_module.mod_oscillation_warning({"session_id": "session-test"})
        assert result == []
