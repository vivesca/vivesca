from __future__ import annotations
"""Tests for the knowledge signal tool."""


import pytest

from metabolon.enzymes.emit import emit
from metabolon.metabolism.signals import SensorySystem


@pytest.fixture
def redirect_collector(tmp_path):
    """Redirect signal collector to tmp_path."""
    orig = SensorySystem.__init__.__defaults__
    SensorySystem.__init__.__defaults__ = (tmp_path / "signals.jsonl",)
    yield tmp_path
    SensorySystem.__init__.__defaults__ = orig


def test_knowledge_signal_useful(redirect_collector):
    result = emit(
        action="knowledge_signal",
        artifact="memory/user_health.md",
        useful=True,
        context="helped with sleep advice",
    )
    assert result.success is True
    assert "memory/user_health.md" in result.message

    collector = SensorySystem()
    signals = collector.recall_all()
    assert len(signals) == 1
    assert signals[0].tool == "knowledge:memory/user_health.md"
    assert signals[0].outcome.value == "success"
    assert signals[0].context == "helped with sleep advice"


def test_knowledge_signal_not_useful(redirect_collector):
    result = emit(
        action="knowledge_signal",
        artifact="memory/stale_project.md",
        useful=False,
    )
    assert result.success is True

    collector = SensorySystem()
    signals = collector.recall_all()
    assert len(signals) == 1
    assert signals[0].outcome.value == "error"


def test_knowledge_signal_multiple(redirect_collector):
    emit(action="knowledge_signal", artifact="ref/epistemics/creativity.md", useful=True)
    emit(action="knowledge_signal", artifact="memory/old_thing.md", useful=False)
    emit(action="knowledge_signal", artifact="skill/rector", useful=True)

    collector = SensorySystem()
    signals = collector.recall_all()
    assert len(signals) == 3
    useful_count = sum(1 for s in signals if s.outcome.value == "success")
    assert useful_count == 2
