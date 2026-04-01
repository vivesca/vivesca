from __future__ import annotations

"""Tests for metabolon.metabolism.repair — immune system / metaprompt-driven healing."""

import configparser
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.metabolism.gates import GateResult
from metabolon.metabolism.repair import (
    ImmuneRequest,
    ImmuneResult,
    _load_conf,
    _mutate,
    immune_response,
)


# ---------------------------------------------------------------------------
# _load_conf
# ---------------------------------------------------------------------------

class TestLoadConf:
    def test_returns_defaults_when_no_conf_file(self, tmp_path: Path, monkeypatch):
        """_load_conf should return defaults even if the .conf file is missing."""
        import metabolon.metabolism.repair as mod

        monkeypatch.setattr(mod, "_CONF_PATH", tmp_path / "nonexistent.conf")
        cfg = mod._load_conf()
        assert cfg.getint("adaptation", "max_adaptation_cycles") == 3

    def test_merges_conf_file_over_defaults(self, tmp_path: Path, monkeypatch):
        """Values in the .conf file should override defaults."""
        import metabolon.metabolism.repair as mod

        conf_file = tmp_path / "repair.conf"
        conf_file.write_text("[adaptation]\nmax_adaptation_cycles = 7\n")
        monkeypatch.setattr(mod, "_CONF_PATH", conf_file)
        cfg = mod._load_conf()
        assert cfg.getint("adaptation", "max_adaptation_cycles") == 7


# ---------------------------------------------------------------------------
# ImmuneRequest
# ---------------------------------------------------------------------------

class TestImmuneRequest:
    def test_basic_construction(self):
        req = ImmuneRequest(
            tool="grep_files",
            current_description="Search files for patterns",
            failure_reason="Too vague",
        )
        assert req.tool == "grep_files"
        assert req.context is None

    def test_with_context(self):
        req = ImmuneRequest(
            tool="grep_files",
            current_description="Search files",
            failure_reason="Too short",
            context="Returned too many results",
        )
        assert req.context == "Returned too many results"

    def test_requires_all_fields(self):
        with pytest.raises(Exception):
            ImmuneRequest()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ImmuneResult
# ---------------------------------------------------------------------------

class TestImmuneResult:
    def test_accepted_result(self):
        gr = GateResult(True, "OK")
        result = ImmuneResult(
            candidate="Improved description here",
            accepted=True,
            gate_result=gr,
            attempts=1,
        )
        assert result.accepted is True
        assert result.candidate == "Improved description here"
        assert result.attempts == 1

    def test_rejected_result(self):
        gr = GateResult(False, "Too short")
        result = ImmuneResult(
            candidate=None,
            accepted=False,
            gate_result=gr,
            attempts=3,
        )
        assert result.accepted is False
        assert result.candidate is None


# ---------------------------------------------------------------------------
# _mutate
# ---------------------------------------------------------------------------

class TestMutate:
    @pytest.mark.asyncio
    async def test_calls_transduce_and_strips_result(self):
        req = ImmuneRequest(
            tool="my_tool",
            current_description="old desc",
            failure_reason="bad output",
            context="extra info",
        )
        with patch("metabolon.metabolism.repair.asyncio.to_thread") as mock_thread:
            mock_thread.return_value = "  revised description with enough words  "
            result = await _mutate(req)
            assert result == "revised description with enough words"
            mock_thread.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_prompt_includes_all_request_fields(self):
        req = ImmuneRequest(
            tool="search_tool",
            current_description="old",
            failure_reason="fails validation",
            context="edge case",
        )
        with patch("metabolon.metabolism.repair.asyncio.to_thread") as mock_thread:
            mock_thread.return_value = "some response"
            await _mutate(req)
            call_args = mock_thread.call_args
            # to_thread(transduce, "glm", prompt) → args = (transduce, "glm", prompt)
            prompt = call_args[0][2]
            assert "search_tool" in prompt
            assert "fails validation" in prompt
            assert "edge case" in prompt
            assert "old" in prompt

    @pytest.mark.asyncio
    async def test_prompt_shows_na_when_no_context(self):
        req = ImmuneRequest(
            tool="t",
            current_description="d",
            failure_reason="f",
        )
        with patch("metabolon.metabolism.repair.asyncio.to_thread") as mock_thread:
            mock_thread.return_value = "response"
            await _mutate(req)
            prompt = mock_thread.call_args[0][2]
            assert "N/A" in prompt


# ---------------------------------------------------------------------------
# immune_response
# ---------------------------------------------------------------------------

class TestImmuneResponse:
    @pytest.mark.asyncio
    async def test_first_attempt_passes(self):
        """If the first mutation passes the gate, return immediately with attempts=1."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )
        long_desc = "This is a sufficiently long candidate description that passes all gate checks"

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.return_value = long_desc
            mock_gate.return_value = GateResult(True, "OK")

            result = await immune_response(req)

            assert result.accepted is True
            assert result.candidate == long_desc
            assert result.attempts == 1
            mock_mutate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_second_attempt_passes(self):
        """First mutation fails the gate, second passes."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )
        short_desc = "short"
        long_desc = "This is a sufficiently long candidate description that passes all gate checks"

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.side_effect = [short_desc, long_desc]
            mock_gate.side_effect = [
                GateResult(False, "Too short"),
                GateResult(True, "OK"),
            ]

            result = await immune_response(req)

            assert result.accepted is True
            assert result.attempts == 2
            assert mock_mutate.await_count == 2

    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        """All adaptation cycles exhausted → rejected result with last gate result."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.return_value = "short"
            mock_gate.return_value = GateResult(False, "Too short")

            result = await immune_response(req, max_adaptation_cycles=3)

            assert result.accepted is False
            assert result.candidate is None
            assert result.attempts == 3
            assert result.gate_result.passed is False
            assert mock_mutate.await_count == 3

    @pytest.mark.asyncio
    async def test_custom_max_adaptation_cycles(self):
        """Explicit max_adaptation_cycles overrides the module-level default."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.return_value = "short"
            mock_gate.return_value = GateResult(False, "Too short")

            result = await immune_response(req, max_adaptation_cycles=1)

            assert result.attempts == 1
            assert mock_mutate.await_count == 1

    @pytest.mark.asyncio
    async def test_uses_module_default_cycles_when_none(self):
        """When max_adaptation_cycles is None, use module-level default."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.return_value = "short"
            mock_gate.return_value = GateResult(False, "Too short")

            # Module default is 3 (from repair.conf)
            result = await immune_response(req, max_adaptation_cycles=None)

            assert result.attempts == 3
            assert mock_mutate.await_count == 3

    @pytest.mark.asyncio
    async def test_last_gate_result_preserved_on_failure(self):
        """On rejection, the gate_result should be from the last attempt."""
        req = ImmuneRequest(
            tool="t", current_description="d", failure_reason="f"
        )

        with patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock) as mock_mutate, \
             patch("metabolon.metabolism.repair.reflex_check") as mock_gate:
            mock_mutate.return_value = "short"
            mock_gate.side_effect = [
                GateResult(False, "Too short"),
                GateResult(False, "Too short"),
                GateResult(False, "Empty description"),
            ]

            result = await immune_response(req, max_adaptation_cycles=3)

            assert result.gate_result.reason == "Empty description"
