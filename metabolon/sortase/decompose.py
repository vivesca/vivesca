from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    spec: str
    files: list[str]
    signal: str = "default"
    prerequisite: str | None = None
    temp_file: str | None = None


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:yaml)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)


def _read_plan(plan_file: Path) -> str:
    return plan_file.read_text(encoding="utf-8")


def _parse_yaml_tasks(raw: str) -> list[TaskSpec]:
    payload = yaml.safe_load(raw)
    if isinstance(payload, dict):
        payload = payload.get("tasks", [])

    tasks: list[TaskSpec] = []
    for idx, item in enumerate(payload or [], start=1):
        if not isinstance(item, dict):
            raise ValueError("YAML task entries must be mappings")
        tasks.append(
            TaskSpec(
                name=item.get("name") or f"task-{idx}",
                description=item.get("description") or item.get("spec") or f"Task {idx}",
                files=list(item.get("files") or []),
                signal=item.get("signal") or "default",
                spec=item.get("spec") or item.get("description") or "",
                prerequisite=item.get("prerequisite"),
            )
        )
    return tasks


def _write_temp_specs(tasks: list[TaskSpec]) -> list[TaskSpec]:
    materialized: list[TaskSpec] = []
    for idx, task in enumerate(tasks, start=1):
        path = Path(tempfile.gettempdir()) / f"sortase-task-{idx}.txt"
        path.write_text(task.spec, encoding="utf-8")
        materialized.append(
            TaskSpec(
                name=task.name,
                description=task.description,
                files=task.files,
                signal=task.signal,
                spec=task.spec,
                prerequisite=task.prerequisite,
                temp_file=str(path),
            )
        )
    return materialized


def _gemini_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _run_gemini_decomposition(plan_text: str, timeout_sec: int) -> str:
    prompt = (
        "Read this plan and decompose it into independent tasks.\n"
        "For each task, output a YAML block:\n"
        "- name: short-kebab-name\n"
        "- description: one line\n"
        "- files: list of files that will be created/modified\n"
        "- signal: rust | algorithmic | multi-file | boilerplate | default\n"
        "- spec: the full self-contained prompt for this task\n\n"
        "Tasks are independent if they touch different files and don't depend on each other's output.\n"
        "If tasks share a dependency (e.g. a shared types file), mark the dependency as a prerequisite task that must run first.\n\n"
        "Plan:\n"
        f"{plan_text}"
    )
    command = ["gemini", "-m", "gemini-3.1-pro-preview", "-p", prompt, "--yolo"]
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=_gemini_env(),
        text=True,
        timeout=timeout_sec,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Gemini decomposition failed")
    return completed.stdout


def decompose_plan(plan_file: str | Path, smart: bool = False, timeout_sec: int = 180) -> list[TaskSpec]:
    path = Path(plan_file)
    plan_text = _read_plan(path)

    if path.suffix.lower() in {".yaml", ".yml"} and not smart:
        return _write_temp_specs(_parse_yaml_tasks(plan_text))

    if not smart:
        return _write_temp_specs(
            [
                TaskSpec(
                    name=path.stem.replace(" ", "-"),
                    description=path.name,
                    files=[],
                    signal="default",
                    spec=plan_text,
                )
            ]
        )

    gemini_output = _strip_fences(_run_gemini_decomposition(plan_text, timeout_sec=timeout_sec))
    return _write_temp_specs(_parse_yaml_tasks(gemini_output))
