#!/usr/bin/env python3
from __future__ import annotations

"""Shared data models for temporal-golem.

Extracted to avoid circular imports between worker.py and workflow.py.
"""

from dataclasses import dataclass, field
from typing import List


# ── Activity result ──────────────────────────────────────────────────


@dataclass
class GolemResult:
    """Outcome of a single golem invocation."""

    provider: str
    task: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def __str__(self) -> str:
        status = "OK" if self.ok else "FAIL"
        return (
            f"[{status}] provider={self.provider} exit={self.exit_code} "
            f"task={self.task!r}"
        )


# ── Workflow input / output ──────────────────────────────────────────


@dataclass
class GolemTaskSpec:
    """A single task to dispatch."""

    provider: str
    task: str


@dataclass
class GolemDispatchInput:
    """Workflow input: a batch of golem tasks."""

    tasks: List[GolemTaskSpec] = field(default_factory=list)


@dataclass
class GolemDispatchOutput:
    """Workflow output: results keyed by provider."""

    results: List[GolemResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0

    def __str__(self) -> str:
        lines = [
            f"GolemDispatch: {self.succeeded}/{self.total} succeeded, "
            f"{self.failed} failed",
        ]
        for r in self.results:
            marker = "OK" if r.ok else "FAIL"
            lines.append(f"  [{marker}] {r.provider}: {r.task!r}")
        return "\n".join(lines)
