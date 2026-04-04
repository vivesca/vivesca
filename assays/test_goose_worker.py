from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


def load_goose_worker():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "goose-worker"
    loader = SourceFileLoader("goose_worker", str(module_path))
    spec = importlib.util.spec_from_loader("goose_worker", loader)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load goose-worker module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompletedProcessStub:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def configure_queue(module, tmp_path: Path) -> Path:
    queue_dir = tmp_path / "task-queue"
    module.QUEUE = queue_dir
    module.PENDING = queue_dir / "pending"
    module.RUNNING = queue_dir / "running"
    module.DONE = queue_dir / "done"
    module.FAILED = queue_dir / "failed"
    return queue_dir


def test_goose_worker_moves_successful_task_to_done(tmp_path: Path, monkeypatch):
    module = load_goose_worker()
    queue_dir = configure_queue(module, tmp_path)
    task_path = queue_dir / "pending" / "sample-task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text("# Sample task\n", encoding="utf-8")

    emitted_signals: list[tuple[str, str]] = []

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/sortase")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcessStub(0, stdout="ok\n", stderr=""),
    )
    monkeypatch.setattr(
        module, "emit_signal", lambda name, content: emitted_signals.append((name, content))
    )

    assert module.main() == 0

    done_path = queue_dir / "done" / "sample-task.md"
    assert done_path.exists()
    assert not (queue_dir / "pending" / "sample-task.md").exists()
    content = done_path.read_text(encoding="utf-8")
    assert "## Result" in content
    assert "**Exit code:** 0" in content
    assert "ok" in content
    assert emitted_signals == [
        ("goose-task-complete-sample-task", "Task sample-task completed successfully."),
    ]


def test_goose_worker_moves_failed_task_to_failed(tmp_path: Path, monkeypatch):
    module = load_goose_worker()
    queue_dir = configure_queue(module, tmp_path)
    task_path = queue_dir / "pending" / "broken_task.md"
    task_path.parent.mkdir(parents=True)
    task_path.write_text("# Broken task\n", encoding="utf-8")

    emitted_signals: list[tuple[str, str]] = []

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/sortase")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcessStub(7, stdout="", stderr="boom\n"),
    )
    monkeypatch.setattr(
        module, "emit_signal", lambda name, content: emitted_signals.append((name, content))
    )

    assert module.main() == 7

    failed_path = queue_dir / "failed" / "broken_task.md"
    assert failed_path.exists()
    content = failed_path.read_text(encoding="utf-8")
    assert "**Exit code:** 7" in content
    assert "boom" in content
    assert emitted_signals == [
        ("goose-task-failed-broken-task", "Task broken_task failed with exit code 7."),
    ]


def test_goose_worker_bootstraps_queue_dirs_when_empty(tmp_path: Path):
    module = load_goose_worker()
    queue_dir = configure_queue(module, tmp_path)

    assert module.main() == 0

    assert (queue_dir / "pending").exists()
    assert (queue_dir / "running").exists()
    assert (queue_dir / "done").exists()
    assert (queue_dir / "failed").exists()
