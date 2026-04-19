"""Worker executor — run a coding task on a provider and capture results."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from mtor.coaching import inject_coaching
from mtor.providers import build_command
from mtor.reflection import capture_reflection, capture_stall_report
from mtor.stall import StallSignal, detect_stall

if TYPE_CHECKING:
    from pathlib import Path

    from mtor.config import MtorConfig, ProviderConfig


@dataclass
class TaskResult:
    provider: str
    exit_code: int
    duration_seconds: int
    output: str
    files_created: int = 0
    reflection: str | None = None
    stall: StallSignal = field(default_factory=lambda: StallSignal("none", ""))
    timestamp: str = ""

    def to_log_entry(self) -> dict:
        return {
            "ts": self.timestamp,
            "provider": self.provider,
            "duration": self.duration_seconds,
            "exit": self.exit_code,
            "files_created": self.files_created,
            "reflection": self.reflection or "",
            "stall": self.stall.stall_type,
            "tail": self.output[-200:] if self.output else "",
        }


def run_task(prompt: str, provider: ProviderConfig, config: MtorConfig) -> TaskResult:
    full_prompt = inject_coaching(prompt, config.coaching_file)
    cmd = build_command(provider, full_prompt, timeout=7200)
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd.args,
            capture_output=True,
            text=True,
            timeout=cmd.timeout,
            env=cmd.env,
            stdin=subprocess.DEVNULL,
            cwd=str(config.workdir),
        )
        exit_code = result.returncode
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        exit_code = 124
        output = "TIMEOUT"
    except FileNotFoundError as exc:
        exit_code = 127
        output = f"Command not found: {exc}"
    duration = int(time.monotonic() - start)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    reflection = capture_reflection()
    stall_report = capture_stall_report()
    files_created = 0
    try:
        git_result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=AM", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(config.workdir),
        )
        if git_result.returncode == 0:
            files_created = len([line for line in git_result.stdout.strip().split("\n") if line])
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    stall = detect_stall(
        exit_code=exit_code,
        duration_seconds=duration,
        output_length=len(output),
        files_created=files_created,
        self_report=stall_report,
    )
    return TaskResult(
        provider=provider.name,
        exit_code=exit_code,
        duration_seconds=duration,
        output=output,
        files_created=files_created,
        reflection=reflection,
        stall=stall,
        timestamp=timestamp,
    )


def log_result(result: TaskResult, log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as fh:
        fh.write(json.dumps(result.to_log_entry()) + "\n")
