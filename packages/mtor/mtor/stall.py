"""Stall detection — classify worker failures by signal type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StallSignal:
    """A detected stall event."""

    stall_type: str
    detail: str

    @property
    def is_stalled(self) -> bool:
        return self.stall_type != "none"


def detect_stall(
    *,
    exit_code: int,
    duration_seconds: int,
    output_length: int,
    files_created: int,
    self_report: str | None = None,
) -> StallSignal:
    if self_report:
        return StallSignal(stall_type="self-reported", detail=self_report.strip())
    if exit_code == 0:
        return StallSignal(stall_type="none", detail="success")
    if files_created == 0 and duration_seconds > 60:
        if output_length > 5000 and duration_seconds > 300:
            return StallSignal(
                stall_type="monologue",
                detail=f"ran {duration_seconds}s, {output_length} chars output, 0 files",
            )
        return StallSignal(
            stall_type="built-nothing", detail=f"ran {duration_seconds}s, 0 files created"
        )
    return StallSignal(stall_type="none", detail=f"exit={exit_code}")


def format_stall_marker(provider: str, signal: StallSignal, duration: int) -> str:
    return f"RIBOSOME_STALL: provider={provider} type={signal.stall_type} duration={duration}s signal={signal.detail}"
