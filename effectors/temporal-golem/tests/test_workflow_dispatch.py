#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import workflow as golem_workflow


class _LoggerStub:
    def info(self, _message: str) -> None:
        pass


def _install_activity_stub(monkeypatch):
    recorded_calls: list[tuple[str, str, int]] = []

    async def fake_execute_activity(_activity, args, **_kwargs):
        task, dispatch_provider, max_turns = args
        recorded_calls.append((task, dispatch_provider, max_turns))
        await asyncio.sleep(0)
        return {
            "task": task,
            "provider": dispatch_provider,
            "success": True,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "rate_limited": False,
        }

    monkeypatch.setattr(golem_workflow.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(golem_workflow.workflow, "time", lambda: 0.0)
    monkeypatch.setattr(golem_workflow.workflow, "logger", _LoggerStub())
    return recorded_calls


def test_cooldowned_provider_tasks_migrate_to_another_provider(monkeypatch):
    recorded_calls = _install_activity_stub(monkeypatch)
    dispatcher = golem_workflow.GolemDispatchWorkflow()

    results = asyncio.run(
        dispatcher._run_pending_queue(
            [{"task": "migrate me", "provider": "zhipu", "max_turns": 25}],
            provider_cooldown_until={"zhipu": 60.0},
        )
    )

    assert recorded_calls == [("migrate me", "infini", 25)]
    assert results[0]["provider"] == "zhipu"
    assert results[0]["dispatch_provider"] == "infini"


def test_non_cooldowned_tasks_keep_original_provider_affinity(monkeypatch):
    recorded_calls = _install_activity_stub(monkeypatch)
    dispatcher = golem_workflow.GolemDispatchWorkflow()

    results = asyncio.run(
        dispatcher._run_pending_queue(
            [
                {"task": "stay on zhipu", "provider": "zhipu", "max_turns": 10},
                {"task": "stay on codex", "provider": "codex", "max_turns": 15},
            ],
        )
    )

    assert recorded_calls == [
        ("stay on zhipu", "zhipu", 10),
        ("stay on codex", "codex", 15),
    ]
    assert {(result["provider"], result["dispatch_provider"]) for result in results} == {
        ("zhipu", "zhipu"),
        ("codex", "codex"),
    }
