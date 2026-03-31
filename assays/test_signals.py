from __future__ import annotations
"""Tests for signal collection and JSONL persistence."""


from datetime import UTC
from typing import Any, cast

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus


def test_signal_model_fields():
    s = Stimulus(
        tool="fasti_list_events",
        outcome=Outcome.success,
        substrate_consumed=340,
        product_released=120,
        response_latency=1200,
    )
    assert s.tool == "fasti_list_events"
    assert s.outcome == "success"
    assert s.error is None
    assert s.correction is None
    assert s.ts is not None  # auto-set


def test_signal_outcome_validation():
    import pytest

    with pytest.raises(ValueError):
        Stimulus(
            tool="x",
            outcome=cast(Any, "invalid"),
            substrate_consumed=0,
            product_released=0,
            response_latency=0,
        )


def test_collector_append_and_read(tmp_path):
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(sensory_surface_path=log)

    s = Stimulus(
        tool="fasti_list_events",
        outcome=Outcome.success,
        substrate_consumed=100,
        product_released=50,
        response_latency=500,
    )
    collector.append(s)

    signals = collector.recall_all()
    assert len(signals) == 1
    assert signals[0].tool == "fasti_list_events"


def test_collector_append_multiple(tmp_path):
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(sensory_surface_path=log)

    for i in range(5):
        collector.append(
            Stimulus(
                tool=f"tool_{i}",
                outcome=Outcome.success,
                substrate_consumed=10,
                product_released=10,
                response_latency=100,
            )
        )

    assert len(collector.recall_all()) == 5


def test_collector_read_since(tmp_path):
    from datetime import datetime, timedelta

    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(sensory_surface_path=log)

    old = Stimulus(
        tool="old",
        outcome=Outcome.success,
        substrate_consumed=10,
        product_released=10,
        response_latency=100,
    )
    # Manually backdate
    old.ts = datetime.now(UTC) - timedelta(days=10)
    collector.append(old)

    new = Stimulus(
        tool="new",
        outcome=Outcome.success,
        substrate_consumed=10,
        product_released=10,
        response_latency=100,
    )
    collector.append(new)

    since = datetime.now(UTC) - timedelta(days=1)
    recent = collector.recall_since(since)
    assert len(recent) == 1
    assert recent[0].tool == "new"


def test_collector_creates_parent_dirs(tmp_path):
    log = tmp_path / "deep" / "nested" / "signals.jsonl"
    collector = SensorySystem(sensory_surface_path=log)
    collector.append(
        Stimulus(
            tool="x",
            outcome=Outcome.success,
            substrate_consumed=1,
            product_released=1,
            response_latency=1,
        )
    )
    assert log.exists()
