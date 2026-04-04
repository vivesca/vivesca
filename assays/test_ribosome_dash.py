import io
import json
import types
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console


def load_ribosome_dash() -> types.ModuleType:
    """Exec the standalone effector into an isolated module object."""
    module = types.ModuleType("ribosome_dash_test")
    module.__file__ = str(Path(__file__).resolve().parents[1] / "effectors" / "ribosome-dash")
    source = Path(module.__file__).read_text()
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


@pytest.fixture
def ribosome_dash() -> types.ModuleType:
    return load_ribosome_dash()


def render_text(renderable) -> str:
    buffer = io.StringIO()
    Console(file=buffer, width=140, force_terminal=False, color_system=None).print(renderable)
    return buffer.getvalue()


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")


def test_parse_ts_strips_fractional_seconds_and_offset(ribosome_dash: types.ModuleType):
    parsed = ribosome_dash.parse_ts("2026-04-02T09:15:27.123456+00:00")
    assert parsed == datetime(2026, 4, 2, 9, 15, 27, tzinfo=UTC)


def test_is_rate_limited_detects_pattern_and_fast_empty_failures(ribosome_dash: types.ModuleType):
    assert ribosome_dash.is_rate_limited(
        {"exit": 1, "duration": 30, "tail": "429 Too Many Requests"}
    )
    assert ribosome_dash.is_rate_limited({"exit": 1, "duration": 3, "tail": " "})
    assert not ribosome_dash.is_rate_limited({"exit": 1, "duration": 90, "tail": "syntax error"})


def test_load_jsonl_filters_window_and_skips_bad_lines(
    ribosome_dash: types.ModuleType, tmp_path: Path
):
    jsonl_path = tmp_path / "ribosome.jsonl"
    now = datetime.now(UTC)
    recent_record = {
        "ts": (now - timedelta(minutes=10)).isoformat(),
        "provider": "infini",
        "exit": 0,
        "duration": 12,
    }
    old_record = {
        "ts": (now - timedelta(hours=3)).isoformat(),
        "provider": "zhipu",
        "exit": 0,
        "duration": 24,
    }
    jsonl_path.write_text(
        "\n".join([json.dumps(recent_record), "{not json}", json.dumps(old_record)]) + "\n"
    )
    ribosome_dash.JSONL_PATH = jsonl_path

    records = ribosome_dash.load_jsonl(window_minutes=60)

    assert records == [recent_record]


def test_count_pending_and_completed_from_queue(ribosome_dash: types.ModuleType, tmp_path: Path):
    queue_path = tmp_path / "translation-queue.md"
    queue_path.write_text(
        "- [ ] first --provider infini\n"
        "- [ ] second\n"
        "- [x] done --provider infini\n"
        "- [ ] third --provider zhipu\n"
    )
    ribosome_dash.QUEUE_PATH = queue_path

    assert dict(ribosome_dash.count_pending_by_provider()) == {
        "infini": 1,
        "unassigned": 1,
        "zhipu": 1,
    }
    assert ribosome_dash.count_total_pending() == 3
    assert ribosome_dash.count_total_completed() == 1


def test_compute_provider_stats_classifies_outcomes(ribosome_dash: types.ModuleType):
    window_records = [
        {"provider": "infini", "exit": 0, "duration": 20, "tail": ""},
        {"provider": "infini", "exit": 1, "duration": 2, "tail": "429 Too Many Requests"},
        {"provider": "infini", "exit": 137, "duration": 5, "tail": ""},
        {"provider": "zhipu", "exit": 1, "duration": 40, "tail": "syntax error"},
    ]
    running = [{"task_id": "run-1", "provider": "infini"}]

    stats = ribosome_dash.compute_provider_stats(window_records, running)

    assert stats["infini"]["active"] == 1
    assert stats["infini"]["completed"] == 1
    assert stats["infini"]["rate_limited"] == 1
    assert stats["infini"]["killed"] == 1
    assert stats["zhipu"]["failed"] == 1


def test_build_json_snapshot_includes_running_progress(
    ribosome_dash: types.ModuleType, tmp_path: Path
):
    now = datetime.now(UTC)
    jsonl_path = tmp_path / "ribosome.jsonl"
    queue_path = tmp_path / "translation-queue.md"
    running_path = tmp_path / "ribosome-running.json"
    cooldowns_path = tmp_path / "ribosome-cooldowns.json"

    write_jsonl(
        jsonl_path,
        [
            {
                "ts": (now - timedelta(minutes=5)).isoformat(),
                "provider": "infini",
                "exit": 0,
                "duration": 120,
                "tail": "",
                "task_id": "done-1",
            }
        ],
    )
    queue_path.write_text("- [ ] pending --provider infini\n- [x] finished --provider infini\n")
    running_path.write_text(
        json.dumps([{"task_id": "run-1", "provider": "infini", "cmd": '"prompt"'}])
    )
    cooldowns_path.write_text("[]")

    ribosome_dash.JSONL_PATH = jsonl_path
    ribosome_dash.QUEUE_PATH = queue_path
    ribosome_dash.RUNNING_JSON_PATH = running_path
    ribosome_dash.COOLDOWNS_PATH = cooldowns_path
    ribosome_dash._task_first_seen["run-1"] = ribosome_dash.time.time() - 60

    snapshot = ribosome_dash.build_json_snapshot(window_minutes=60)

    assert snapshot["pending"] == 1
    assert snapshot["completed"] == 1
    assert snapshot["pending_by_provider"] == {"infini": 1}
    assert snapshot["running_tasks"][0]["task_id"] == "run-1"
    assert snapshot["running_tasks"][0]["progress"] == pytest.approx(0.5, rel=0.2)
    assert snapshot["recent_events"][0]["outcome"] == "success"


def test_build_running_tasks_table_renders_health_and_dispatch(ribosome_dash: types.ModuleType):
    ribosome_dash._task_first_seen["run-1"] = ribosome_dash.time.time() - 260
    running = [
        {
            "task_id": "run-1",
            "provider": "infini",
            "dispatch_provider": "zhipu",
            "cmd": 'ribosome "repair the queue"',
        }
    ]
    provider_stats = {
        "infini": {
            "active": 1,
            "completed": 1,
            "failed": 3,
            "rate_limited": 0,
            "killed": 0,
            "total_duration": 400,
            "success_count": 1,
            "total_count": 4,
        }
    }

    table = ribosome_dash.build_running_tasks_table(
        running,
        avg_duration_by_provider={"infini": 100.0},
        provider_stats=provider_stats,
    )
    output = render_text(table)

    assert "run-1" in output
    assert "stalled" in output
    assert "repair the queue" in output
    assert "zhipu" in output


def test_build_dashboard_renders_sections(ribosome_dash: types.ModuleType, tmp_path: Path):
    now = datetime.now(UTC)
    jsonl_path = tmp_path / "ribosome.jsonl"
    queue_path = tmp_path / "translation-queue.md"
    running_path = tmp_path / "ribosome-running.json"
    cooldowns_path = tmp_path / "ribosome-cooldowns.json"

    write_jsonl(
        jsonl_path,
        [
            {
                "ts": (now - timedelta(minutes=8)).isoformat(),
                "provider": "infini",
                "exit": 0,
                "duration": 100,
                "tail": "",
                "task_id": "done-1",
            },
            {
                "ts": (now - timedelta(minutes=3)).isoformat(),
                "provider": "zhipu",
                "exit": 1,
                "duration": 2,
                "tail": "429 quota exceeded",
                "task_id": "fail-1",
            },
        ],
    )
    queue_path.write_text(
        "- [ ] queued --provider infini\n"
        "- [ ] queued2 --provider zhipu\n"
        "- [x] finished --provider infini\n"
    )
    running_path.write_text(
        json.dumps([{"task_id": "run-1", "provider": "infini", "cmd": '"prompt"'}])
    )
    cooldowns_path.write_text(
        json.dumps(
            [{"provider": "zhipu", "expires_at": (now + timedelta(minutes=15)).isoformat()}]
        )
    )

    ribosome_dash.JSONL_PATH = jsonl_path
    ribosome_dash.QUEUE_PATH = queue_path
    ribosome_dash.RUNNING_JSON_PATH = running_path
    ribosome_dash.COOLDOWNS_PATH = cooldowns_path
    ribosome_dash._task_first_seen["run-1"] = ribosome_dash.time.time() - 30

    dashboard = ribosome_dash.build_dashboard(window_minutes=60)
    output = render_text(dashboard)

    assert "Ribosome Task Monitor" in output
    assert "Running Tasks" in output
    assert "Drain Timeline" in output
    assert "Recent Events" in output
    assert "Cooldowns" in output
    assert "infini" in output
    assert "zhipu" in output


def test_main_exits_with_error_when_jsonl_missing(
    ribosome_dash: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    missing_path = Path("/tmp/does-not-exist-ribosome-jsonl")
    ribosome_dash.JSONL_PATH = missing_path
    monkeypatch.setattr("sys.argv", ["ribosome-dash"])

    with pytest.raises(SystemExit) as excinfo:
        ribosome_dash.main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "No data file found" in captured.err
    assert "Start ribosome-daemon first." in captured.err


def test_main_once_honors_window_arg_and_prints_dashboard(
    ribosome_dash: types.ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    jsonl_path = tmp_path / "ribosome.jsonl"
    write_jsonl(
        jsonl_path,
        [{"ts": datetime.now(UTC).isoformat(), "provider": "infini", "exit": 0, "duration": 1}],
    )
    ribosome_dash.JSONL_PATH = jsonl_path

    seen: dict[str, object] = {}

    def fake_build_dashboard(window_minutes: int):
        seen["window_minutes"] = window_minutes
        return "panel-sentinel"

    monkeypatch.setattr("sys.argv", ["ribosome-dash", "--once", "--window", "15"])
    ribosome_dash.build_dashboard = fake_build_dashboard

    with patch("rich.console.Console.print") as print_mock:
        ribosome_dash.main()

    assert seen["window_minutes"] == 15
    print_mock.assert_called_once_with("panel-sentinel")
