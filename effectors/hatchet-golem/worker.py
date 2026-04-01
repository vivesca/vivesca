#!/usr/bin/env python3
"""Hatchet worker for golem task orchestration.

Uses @hatchet.task (standalone tasks) with per-provider concurrency.
Compare with temporal-golem/ for head-to-head eval.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from hatchet_sdk import ConcurrencyExpression, ConcurrencyLimitStrategy, Hatchet

GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

hatchet = Hatchet()


def _run_golem(input, context, provider: str) -> dict:
    """Shared golem execution logic."""
    task = input.get("task", "") if isinstance(input, dict) else str(input)
    max_turns = input.get("max_turns", 50) if isinstance(input, dict) else 50

    cmd = [
        "bash", str(GOLEM_SCRIPT),
        "--provider", provider,
        "--max-turns", str(max_turns),
        task,
    ]

    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=1800,
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


@hatchet.task(
    name="golem-zhipu",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'zhipu'",
        max_runs=8,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
def golem_zhipu(input, context):
    return _run_golem(input, context, "zhipu")


@hatchet.task(
    name="golem-infini",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'infini'",
        max_runs=8,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
def golem_infini(input, context):
    return _run_golem(input, context, "infini")


@hatchet.task(
    name="golem-volcano",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'volcano'",
        max_runs=16,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
def golem_volcano(input, context):
    return _run_golem(input, context, "volcano")


@hatchet.task(
    name="golem-gemini",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'gemini'",
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
)
def golem_gemini(input, context):
    return _run_golem(input, context, "gemini")


def main():
    worker = hatchet.worker(
        "golem-worker",
        workflows=[golem_zhipu, golem_infini, golem_volcano, golem_gemini],
    )
    print("Hatchet golem worker started")
    worker.start()


if __name__ == "__main__":
    main()
