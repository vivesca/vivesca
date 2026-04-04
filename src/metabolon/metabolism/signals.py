"""Stimulus collection and JSONL persistence."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from metabolon.locus import signals_log


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


DEFAULT_LOG = signals_log


class SensorySystem:
    """Append-only JSONL signal log."""

    def __init__(self, sensory_surface_path: Path = DEFAULT_LOG):
        self.sensory_surface_path = sensory_surface_path

    def append(self, signal: Stimulus) -> None:
        self.sensory_surface_path.parent.mkdir(parents=True, exist_ok=True)
        with self.sensory_surface_path.open("a") as f:
            f.write(signal.model_dump_json() + "\n")

    def recall_all(self) -> list[Stimulus]:
        if not self.sensory_surface_path.exists():
            return []
        signals = []
        for line in self.sensory_surface_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                signals.append(Stimulus.model_validate_json(line))
            except Exception:
                continue  # skip non-Stimulus entries (e.g. anam-scan)
        return signals

    def recall_since(self, since: datetime) -> list[Stimulus]:
        return [s for s in self.recall_all() if s.ts >= since]
