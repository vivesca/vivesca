from __future__ import annotations

"""Tests for quorum — multi-model deliberation engine."""

from pathlib import Path

import pytest


class TestContribution:
    def test_fields(self):
        from metabolon.organelles.quorum import Contribution
        c = Contribution(model="claude", content="hello", phase="blind")
        assert c.model == "claude"
        assert c.content == "hello"
        assert c.phase == "blind"


class TestDeliberation:
    def test_summary(self):
        from metabolon.organelles.quorum import Deliberation
        d = Deliberation(question="test?", mode="quick", decision="Yes.", elapsed_s=2.5)
        summary = d.summary()
        assert "Yes." in summary
        assert "quick" in summary

    def test_summary_with_dissents(self):
        from metabolon.organelles.quorum import Deliberation
        d = Deliberation(
            question="test?", mode="council",
            decision="No.", dissents=["But maybe yes."],
            elapsed_s=5.0,
        )
        summary = d.summary()
        assert "Dissent" in summary
        assert "But maybe yes." in summary

    def test_transcript(self):
        from metabolon.organelles.quorum import Contribution, Deliberation
        d = Deliberation(
            question="Should we?", mode="quick",
            contributions=[
                Contribution(model="claude", content="Yes, because...", phase="blind"),
                Contribution(model="gemini", content="No, because...", phase="blind"),
            ],
            decision="Yes.",
            elapsed_s=3.0,
        )
        transcript = d.transcript()
        assert "Should we?" in transcript
        assert "[blind] claude" in transcript
        assert "[blind] gemini" in transcript

    def test_save(self, tmp_path):
        from metabolon.organelles.quorum import Deliberation
        from unittest.mock import patch
        import metabolon.organelles.quorum as qm
        with patch.object(qm, "COUNCIL_DIR", tmp_path):
            d = Deliberation(question="Test question", mode="quick", decision="Answer.")
            path = d.save()
        assert path.exists()
        assert "Test question" in path.read_text()


class TestPromptTemplates:
    def test_blind_prompt(self):
        from metabolon.organelles.quorum import _blind_prompt
        result = _blind_prompt("What is AI?")
        assert "What is AI?" in result
        assert "independently" in result.lower()

    def test_blind_prompt_with_persona(self):
        from metabolon.organelles.quorum import _blind_prompt
        result = _blind_prompt("What is AI?", persona="banking consultant")
        assert "banking consultant" in result

    def test_debate_prompt(self):
        from metabolon.organelles.quorum import _debate_prompt, Contribution
        prior = [
            Contribution(model="claude", content="Answer A", phase="blind"),
            Contribution(model="gemini", content="Answer B", phase="blind"),
        ]
        result = _debate_prompt("test?", prior, "claude")
        assert "gemini" in result  # should show other's answer
        assert "Answer B" in result

    def test_judge_prompt(self):
        from metabolon.organelles.quorum import _judge_prompt, Contribution
        contribs = [Contribution(model="claude", content="Yes", phase="blind")]
        result = _judge_prompt("test?", contribs)
        assert "DECISION" in result
        assert "DISSENT" in result
