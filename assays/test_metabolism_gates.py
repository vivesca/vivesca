from __future__ import annotations

"""Tests for metabolon.metabolism.gates — reflex_check + taste."""

from unittest.mock import patch

import pytest

from metabolon.metabolism.gates import (
    MAX_WORDS,
    MIN_WORDS,
    GateResult,
    reflex_check,
    taste,
)

# ── GateResult ──────────────────────────────────────────────────────────


class TestGateResult:
    def test_fields(self):
        g = GateResult(passed=True, reason="OK")
        assert g.passed is True
        assert g.reason == "OK"


# ── reflex_check ────────────────────────────────────────────────────────


class TestReflexCheck:
    def _make_text(self, n_words: int) -> str:
        return " ".join(["word"] * n_words)

    def test_empty_string(self):
        r = reflex_check("")
        assert r.passed is False
        assert "Empty" in r.reason

    def test_whitespace_only(self):
        r = reflex_check("   \t  ")
        assert r.passed is False
        assert "Empty" in r.reason

    def test_too_short(self):
        r = reflex_check(self._make_text(MIN_WORDS - 1))
        assert r.passed is False
        assert "Too short" in r.reason
        assert str(MIN_WORDS - 1) in r.reason

    def test_min_words_exact(self):
        r = reflex_check(self._make_text(MIN_WORDS))
        assert r.passed is True
        assert r.reason == "OK"

    def test_too_long(self):
        r = reflex_check(self._make_text(MAX_WORDS + 1))
        assert r.passed is False
        assert "Too long" in r.reason

    def test_max_words_exact(self):
        r = reflex_check(self._make_text(MAX_WORDS))
        assert r.passed is True
        assert r.reason == "OK"

    def test_normal_length(self):
        r = reflex_check(self._make_text(50))
        assert r.passed is True

    def test_strips_whitespace(self):
        r = reflex_check("  " + self._make_text(MIN_WORDS) + "  ")
        assert r.passed is True


# ── taste ───────────────────────────────────────────────────────────────
# transduce is imported inside the function body via
# `from metabolon.symbiont import transduce`, so we patch where
# it is looked up: metabolon.symbiont.transduce.


class TestTaste:
    @pytest.mark.asyncio
    @patch("metabolon.symbiont.transduce", return_value="PASS")
    async def test_pass(self, mock_transduce):
        result = await taste("my_tool", "original desc", "new desc")
        assert result.passed is True
        assert "PASS" in result.reason
        mock_transduce.assert_called_once()
        assert mock_transduce.call_args[0][0] == "haiku"

    @pytest.mark.asyncio
    @patch("metabolon.symbiont.transduce", return_value="FAIL: too vague")
    async def test_fail_with_reason(self, mock_transduce):
        result = await taste("my_tool", "original desc", "vague desc")
        assert result.passed is False
        assert "too vague" in result.reason

    @pytest.mark.asyncio
    @patch("metabolon.symbiont.transduce", return_value="FAIL:")
    async def test_fail_empty_reason(self, mock_transduce):
        result = await taste("my_tool", "original", "variant")
        assert result.passed is False
        assert "LLM judge rejected" in result.reason

    @pytest.mark.asyncio
    @patch("metabolon.symbiont.transduce", return_value="PASS\n")
    async def test_pass_with_trailing_whitespace(self, mock_transduce):
        result = await taste("tool", "orig", "variant")
        assert result.passed is True

    @pytest.mark.asyncio
    @patch(
        "metabolon.symbiont.transduce",
        return_value="FAIL: description is misleading",
    )
    async def test_prompt_contains_tool_info(self, mock_transduce):
        await taste("search_tool", "finds things", "loses things")
        prompt_arg = mock_transduce.call_args[0][1]
        assert "search_tool" in prompt_arg
        assert "finds things" in prompt_arg
        assert "loses things" in prompt_arg
