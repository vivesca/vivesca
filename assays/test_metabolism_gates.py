"""Tests for metabolon.metabolism.gates — reflex_check + taste."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from metabolon.metabolism.gates import reflex_check, taste, GateResult, MIN_WORDS, MAX_WORDS


# ── GateResult dataclass ─────────────────────────────────────────────

class TestGateResult:
    def test_fields(self):
        r = GateResult(passed=True, reason="OK")
        assert r.passed is True
        assert r.reason == "OK"

    def test_failed(self):
        r = GateResult(passed=False, reason="bad")
        assert r.passed is False

    def test_equality(self):
        a = GateResult(True, "OK")
        b = GateResult(True, "OK")
        assert a == b


# ── reflex_check ─────────────────────────────────────────────────────

class TestReflexCheck:
    """Pure-logic tests — no mocks needed."""

    def test_valid_passes(self):
        desc = "Fetch calendar events for a specific date and return them as JSON."
        result = reflex_check(desc)
        assert result.passed is True
        assert result.reason == "OK"

    def test_empty_string_fails(self):
        result = reflex_check("")
        assert result.passed is False
        assert "empty" in result.reason.lower()

    def test_whitespace_only_fails(self):
        result = reflex_check("   \n\t  ")
        assert result.passed is False
        assert "empty" in result.reason.lower()

    def test_too_short_fails(self):
        result = reflex_check("List events.")
        # "List events." is 2 words, min is 5
        assert result.passed is False
        assert "too short" in result.reason.lower()
        assert "2 words" in result.reason

    def test_exactly_min_words_passes(self):
        # MIN_WORDS words exactly
        desc = " ".join(["word"] * MIN_WORDS)
        result = reflex_check(desc)
        assert result.passed is True

    def test_one_below_min_words_fails(self):
        desc = " ".join(["word"] * (MIN_WORDS - 1))
        result = reflex_check(desc)
        assert result.passed is False
        assert "too short" in result.reason.lower()

    def test_too_long_fails(self):
        desc = " ".join(["word"] * (MAX_WORDS + 10))
        result = reflex_check(desc)
        assert result.passed is False
        assert "too long" in result.reason.lower()

    def test_exactly_max_words_passes(self):
        desc = " ".join(["word"] * MAX_WORDS)
        result = reflex_check(desc)
        assert result.passed is True

    def test_one_above_max_words_fails(self):
        desc = " ".join(["word"] * (MAX_WORDS + 1))
        result = reflex_check(desc)
        assert result.passed is False
        assert "too long" in result.reason.lower()

    def test_strips_whitespace_before_check(self):
        # After strip, this is empty
        result = reflex_check("   \n   ")
        assert result.passed is False

    def test_reason_includes_word_count_on_short(self):
        result = reflex_check("one two")
        assert "2 words" in result.reason
        assert str(MIN_WORDS) in result.reason

    def test_reason_includes_word_count_on_long(self):
        desc = " ".join(["x"] * (MAX_WORDS + 5))
        result = reflex_check(desc)
        assert str(MAX_WORDS + 5) in result.reason
        assert str(MAX_WORDS) in result.reason


# ── taste (async, LLM-backed) ────────────────────────────────────────

class TestTaste:
    """taste() delegates to metabolon.symbiont.transduce. Mock it."""

    def _run(self, *args, **kwargs):
        return asyncio.run(taste(*args, **kwargs))

    @patch("metabolon.symbiont.transduce", return_value="PASS")
    def test_pass_response(self, mock_transduce):
        result = self._run("my_tool", "original desc", "new desc")
        assert result.passed is True
        assert "PASS" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="PASS - looks good")
    def test_pass_with_extra_text(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is True

    @patch("metabolon.symbiont.transduce", return_value="FAIL: misleading")
    def test_fail_with_reason(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is False
        assert "misleading" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="FAIL: ")
    def test_fail_empty_reason_gets_default(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is False
        assert "LLM judge rejected" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="FAIL: completely wrong description")
    def test_fail_reason_preserved(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is False
        assert "completely wrong description" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="FAIL:something")
    def test_fail_no_space_after_colon(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is False
        assert "something" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="FAIL:   padded   ")
    def test_fail_strips_whitespace_from_reason(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert "padded" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="UNSURE maybe")
    def test_unexpected_response_treated_as_fail(self, mock_transduce):
        result = self._run("tool", "old", "new")
        assert result.passed is False
        assert "UNSURE maybe" in result.reason

    @patch("metabolon.symbiont.transduce", return_value="PASS")
    def test_prompt_contains_tool_name(self, mock_transduce):
        self._run("calendar_fetcher", "old desc", "new desc")
        call_args = mock_transduce.call_args
        prompt = call_args[0][1]  # second positional arg is prompt
        assert "calendar_fetcher" in prompt

    @patch("metabolon.symbiont.transduce", return_value="PASS")
    def test_prompt_contains_descriptions(self, mock_transduce):
        self._run("tool", "founder text here", "variant text here")
        call_args = mock_transduce.call_args
        prompt = call_args[0][1]
        assert "founder text here" in prompt
        assert "variant text here" in prompt

    @patch("metabolon.symbiont.transduce", return_value="PASS")
    def test_calls_haiku_model(self, mock_transduce):
        self._run("tool", "old", "new")
        call_args = mock_transduce.call_args
        assert call_args[0][0] == "haiku"  # first positional arg is model
