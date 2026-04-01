#!/usr/bin/env python3
"""Hatchet worker for golem task orchestration.

Dispatches golem commands as Hatchet workflow steps with per-provider
concurrency groups. Compare with temporal-golem/ for head-to-head eval.

Usage:
    python3 worker.py              # Start worker
    python3 worker.py submit ...   # Submit a task (see --help)
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from hatchet_sdk import ConcurrencyExpression, ConcurrencyLimitStrategy, Hatchet

GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

hatchet = Hatchet()


# === Workflows with per-provider concurrency ===

@hatchet.workflow(
    name="golem-zhipu",
    concurrency=ConcurrencyExpression(
        max_runs=8,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
class GolemZhipu:
    @hatchet.step(timeout="30m")
    def run(self, context) -> dict:
        return _run_golem(context, "zhipu")


@hatchet.workflow(
    name="golem-infini",
    concurrency=ConcurrencyExpression(
        max_runs=8,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
class GolemInfini:
    @hatchet.step(timeout="30m")
    def run(self, context) -> dict:
        return _run_golem(context, "infini")


@hatchet.workflow(
    name="golem-volcano",
    concurrency=ConcurrencyExpression(
        max_runs=16,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
class GolemVolcano:
    @hatchet.step(timeout="30m")
    def run(self, context) -> dict:
        return _run_golem(context, "volcano")


@hatchet.workflow(
    name="golem-gemini",
    concurrency=ConcurrencyExpression(
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
class GolemGemini:
    @hatchet.step(timeout="30m")
    def run(self, context) -> dict:
        return _run_golem(context, "gemini")


# === Shared execution logic ===

def _run_golem(context, provider: str) -> dict:
    """Execute a golem task as a subprocess."""
    input_data = context.workflow_input()
    task = input_data.get("task", "")
    max_turns = input_data.get("max_turns", 50)

    cmd = [
        "bash", str(GOLEM_SCRIPT),
        "--provider", provider,
        "--max-turns", str(max_turns),
        task,
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 min
        env={**os.environ, "GOLEM_PROVIDER": provider},
    )

    return {
        "task": task[:200],
        "provider": provider,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[:4000],
        "stderr": proc.stderr[:2000],
        "success": proc.returncode == 0,
    }


# === Worker entry point ===

def main():
    worker = hatchet.worker(
        "golem-worker",
        workflows=[GolemZhipu, GolemInfini, GolemVolcano, GolemGemini],
    )
    print("Hatchet golem worker started")
    worker.start()


if __name__ == "__main__":
    main()
