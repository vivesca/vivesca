"""Stimulus collection and JSONL persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class Outcome(StrEnum):
    success = "success"
    error = "error"
    correction = "correction"
    reinvocation = "reinvocation"


class Stimulus(BaseModel):
    """A single tool-call observation — one sensory event in the organism."""

    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool: str
    outcome: Outcome
    substrate_consumed: int = 0  # metabolic input (tokens absorbed)
    product_released: int = 0  # metabolic output (tokens emitted)
    response_latency: int = 0  # enzymatic/synaptic response time in ms
    error: str | None = None
    correction: str | None = None
    context: str | None = None


DEFAULT_LOG = Path.home() / ".local" / "share" / "vivesca" / "signals.jsonl"


class SensorySystem:
    """Append-only JSONL signal log."""

    def __init__(self, cortex_path: Path = DEFAULT_LOG):
        self.cortex_path = cortex_path

    def append(self, signal: Stimulus) -> None:
        self.cortex_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cortex_path.open("a") as f:
            f.write(signal.model_dump_json() + "\n")

    def read_all(self) -> list[Stimulus]:
        if not self.cortex_path.exists():
            return []
        signals = []
        for line in self.cortex_path.read_text().splitlines():
            if line.strip():
                signals.append(Stimulus.model_validate_json(line))
        return signals

    def read_since(self, since: datetime) -> list[Stimulus]:
        return [s for s in self.read_all() if s.ts >= since]
