from pathlib import Path
from unittest.mock import patch, MagicMock
from mtor.config import MtorConfig, ProviderConfig
from mtor.worker import TaskResult, run_task, log_result

def _test_provider():
    return ProviderConfig(name="test", url="https://example.com/v1", model="test-model", key_env="TEST_MTOR_KEY", harness="claude")

def test_task_result_log_entry():
    result = TaskResult(provider="zhipu", exit_code=0, duration_seconds=120, output="done", files_created=3, timestamp="2026-04-06T00:00:00Z")
    entry = result.to_log_entry()
    assert entry["provider"] == "zhipu"
    assert entry["exit"] == 0

def test_log_result_appends(tmp_path: Path):
    log_file = tmp_path / "test.jsonl"
    result = TaskResult(provider="test", exit_code=0, duration_seconds=10, output="ok", timestamp="2026-04-06T00:00:00Z")
    log_result(result, log_file)
    log_result(result, log_file)
    assert len(log_file.read_text().strip().split("\n")) == 2

@patch("mtor.worker.subprocess.run")
@patch("mtor.worker.capture_reflection", return_value=None)
@patch("mtor.worker.capture_stall_report", return_value=None)
def test_run_task_success(mock_stall, mock_refl, mock_run, monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_MTOR_KEY", "sk-test")
    mock_run.return_value = MagicMock(returncode=0, stdout="implemented", stderr="")
    config = MtorConfig(workdir=tmp_path)
    result = run_task("fix bug", _test_provider(), config)
    assert result.exit_code == 0
    assert result.provider == "test"
