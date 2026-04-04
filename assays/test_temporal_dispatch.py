"""Tests for polysome/dispatch.py — queue parsing, marking, and dispatch logic."""

import asyncio
import contextlib
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Load the effector via exec (standard pattern for effectors) ───────


def _load_dispatch():
    """Load dispatch.py by exec-ing its source into an isolated namespace."""
    source = (Path.home() / "germline/effectors/polysome/dispatch.py").read_text()
    ns: dict = {"__name__": "dispatch_under_test"}
    exec(source, ns)
    return ns


_mod = _load_dispatch()

parse_queue = _mod["parse_queue"]
mark_done = _mod["mark_done"]
mark_failed = _mod["mark_failed"]
log = _mod["log"]
main = _mod["main"]
QUEUE_FILE = _mod["QUEUE_FILE"]
LOG_FILE = _mod["LOG_FILE"]


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _use_tmp_queue(tmp_path: Path, monkeypatch):
    """Redirect QUEUE_FILE and LOG_FILE to tmp for every test."""
    qfile = tmp_path / "translation-queue.md"
    lfile = tmp_path / "dispatch.log"
    monkeypatch.setitem(_mod, "QUEUE_FILE", qfile)
    monkeypatch.setitem(_mod, "LOG_FILE", lfile)
    # Also patch the module-level references that functions close over
    # Since functions reference QUEUE_FILE via the module global dict, setitem works.
    return qfile, lfile


def _write_queue(path: Path, content: str) -> None:
    """Write content to the queue file."""
    path.write_text(content)


# ── parse_queue tests ─────────────────────────────────────────────────


def test_parse_queue_empty_file(tmp_path):
    """Empty queue file returns no tasks."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, "")
    assert parse_queue() == []


def test_parse_queue_no_file(tmp_path):
    """Missing queue file returns no tasks."""
    qf = tmp_path / "nonexistent.md"
    # Patch QUEUE_FILE to the nonexistent path
    _mod["QUEUE_FILE"] = qf
    assert parse_queue() == []


def test_parse_queue_pending_tasks(tmp_path):
    """Parses - [ ] lines with backtick-enclosed commands."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        ### Section header
        - [ ] `ribosome [t-abc123] --provider zhipu --max-turns 30 "do a thing"`
        - [ ] `ribosome [t-def456] --provider volcano --max-turns 50 "do another"`
    """),
    )
    tasks = parse_queue()
    assert len(tasks) == 2
    # (line_num, prompt, provider, task_id, max_turns)
    assert tasks[0][1] == "do a thing"  # prompt
    assert tasks[0][2] == "zhipu"  # provider
    assert tasks[0][3] == "t-abc123"  # task_id
    assert tasks[0][4] == 30  # max_turns

    assert tasks[1][1] == "do another"
    assert tasks[1][2] == "volcano"
    assert tasks[1][3] == "t-def456"
    assert tasks[1][4] == 50


def test_parse_queue_urgent_tasks(tmp_path):
    """Parses - [!!] lines (urgent priority)."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf, '- [!!] `ribosome [t-a1b2c3] --provider codex --max-turns 40 "fix critical bug"`\n'
    )
    tasks = parse_queue()
    assert len(tasks) == 1
    assert tasks[0][2] == "codex"
    assert tasks[0][3] == "t-a1b2c3"


def test_parse_queue_default_provider(tmp_path):
    """Tasks without --provider default to 'zhipu'."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome "just run it"`\n')
    tasks = parse_queue()
    assert len(tasks) == 1
    assert tasks[0][2] == "zhipu"


def test_parse_queue_default_max_turns(tmp_path):
    """Tasks without --max-turns default to 50."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome --provider infini "no max turns set"`\n')
    tasks = parse_queue()
    assert len(tasks) == 1
    assert tasks[0][4] == 50


def test_parse_queue_auto_task_id(tmp_path):
    """Tasks without [t-XXXX] get auto-generated hash-based task IDs."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome --provider zhipu "auto id task"`\n')
    tasks = parse_queue()
    assert len(tasks) == 1
    # Auto-generated IDs are hash-based: t-XXXXXX
    assert tasks[0][3].startswith("t-")
    assert len(tasks[0][3]) == 8  # "t-" + 6 hex chars


def test_parse_queue_ignores_completed_tasks(tmp_path):
    """Lines with - [x] or - [!] are skipped."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [x] `ribosome [t-d0ne11] --provider zhipu "completed"`
        - [!] `ribosome [t-fa1l22] --provider zhipu "failed"`
        - [ ] `ribosome [t-0badbe] --provider zhipu "pending"`
    """),
    )
    tasks = parse_queue()
    assert len(tasks) == 1
    assert tasks[0][3] == "t-0badbe"


def test_parse_queue_ignores_non_task_lines(tmp_path):
    """Lines without backtick commands are skipped."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        ### Section header
        Some explanatory text
        - [ ] 
    """),
    )
    tasks = parse_queue()
    assert tasks == []


def test_parse_queue_line_numbers(tmp_path):
    """Line numbers correspond to actual file line indices."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        ### Header
        - [ ] `ribosome [t-11ne33] --provider zhipu "line 1"`
    """),
    )
    # "### Header" is line 0, task is line 1 (dedent removes leading newline)
    tasks = parse_queue()
    assert len(tasks) == 1
    assert tasks[0][0] == 1  # line_num


def test_parse_queue_prompt_is_full_cmd_when_no_quotes(tmp_path):
    """When no quoted prompt, the full backtick content is used as prompt."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, "- [ ] `ribosome --provider infini --max-turns 20`\n")
    tasks = parse_queue()
    assert len(tasks) == 1
    # prompt_match returns None, so prompt = cmd (full backtick content, with auto-injected task ID)
    assert "--provider infini --max-turns 20" in tasks[0][1]


# ── mark_done tests ───────────────────────────────────────────────────


def test_mark_done_pending_task(tmp_path):
    """Marking a pending - [ ] task changes it to - [x]."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome [t-abc] --provider zhipu "task"`\n')
    mark_done(0)
    content = qf.read_text()
    assert "- [x] " in content
    assert "- [ ] " not in content


def test_mark_done_urgent_task(tmp_path):
    """Marking an urgent - [!!] task changes it to - [x]."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [!!] `ribosome [t-abc] --provider zhipu "urgent task"`\n')
    mark_done(0)
    content = qf.read_text()
    assert "- [x] " in content
    assert "- [!!] " not in content


def test_mark_done_out_of_range(tmp_path):
    """Marking a line beyond file length is a no-op."""
    qf = tmp_path / "translation-queue.md"
    original = '- [ ] `ribosome "task"`\n'
    _write_queue(qf, original)
    mark_done(999)
    assert qf.read_text() == original


def test_mark_done_preserves_other_lines(tmp_path):
    """Marking one line doesn't affect others."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-a] --provider zhipu "first"`
        - [ ] `ribosome [t-b] --provider zhipu "second"`
    """),
    )
    mark_done(0)
    lines = qf.read_text().splitlines()
    assert "- [x] " in lines[0]
    assert "- [ ] " in lines[1]


# ── mark_failed tests ─────────────────────────────────────────────────


def test_mark_failed_pending_task_retries_first(tmp_path):
    """First failure on a pending task adds (retry), keeps as [ ]."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome [t-abc] --provider zhipu "task"`\n')
    result = mark_failed(0)
    content = qf.read_text()
    assert result["retried"] is True
    assert "(retry)" in content
    assert "- [ ] " in content  # stays pending for retry


def test_mark_failed_pending_task_permanent_on_second(tmp_path):
    """Second failure (already has retry) marks as permanently failed [!]."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [ ] `ribosome [t-abc] --provider zhipu "task (retry)"`\n')
    result = mark_failed(0)
    content = qf.read_text()
    assert result["retried"] is False
    assert "- [!] " in content


def test_mark_failed_urgent_task_retries_first(tmp_path):
    """First failure on an urgent task adds (retry), keeps as [!!]."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, '- [!!] `ribosome [t-abc] --provider zhipu "urgent"`\n')
    result = mark_failed(0)
    content = qf.read_text()
    assert result["retried"] is True
    assert "(retry)" in content


def test_mark_failed_out_of_range(tmp_path):
    """Marking a line beyond file length is a no-op."""
    qf = tmp_path / "translation-queue.md"
    original = '- [ ] `ribosome "task"`\n'
    _write_queue(qf, original)
    mark_failed(999)
    assert qf.read_text() == original


# ── (retry) suffix stripping ───────────────────────────────────────────


def test_retry_suffix_stripped(tmp_path):
    """(retry) suffix injected by mark_failed is stripped from the prompt."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf, '- [ ] `ribosome [t-abc123] --provider zhipu --max-turns 30 "do a thing (retry)"`\n'
    )
    tasks = parse_queue()
    assert len(tasks) == 1
    prompt = tasks[0][1]
    assert "(retry)" not in prompt
    assert "do a thing" in prompt


# ── dispatch_all tests (async) ────────────────────────────────────────


def test_dispatch_all_no_pending(tmp_path, capsys):
    """dispatch_all with empty queue returns 0."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(qf, "")
    result = asyncio.run(_mod["dispatch_all"]())
    assert result == 0


def test_dispatch_all_dry_run(tmp_path, capsys):
    """dispatch_all with dry_run=True returns count without dispatching."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-abc] --provider zhipu --max-turns 30 "test task"`
    """),
    )
    result = asyncio.run(_mod["dispatch_all"](dry_run=True))
    assert result == 1
    # Queue should NOT be modified in dry run
    assert "- [ ] " in qf.read_text()
    # Should log dry run
    captured = capsys.readouterr()
    assert "[DRY]" in captured.out


def test_dispatch_all_starts_workflow(tmp_path):
    """dispatch_all starts a Temporal workflow and returns count of started tasks."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-abc] --provider zhipu --max-turns 30 "Fix X. Test: uv run pytest assays/test_foo.py -x"`
    """),
    )

    mock_client = AsyncMock()
    mock_handle = MagicMock()
    mock_client.start_workflow = AsyncMock(return_value=mock_handle)

    mock_workflow_mod = MagicMock()

    with patch.dict("sys.modules", {"workflow": mock_workflow_mod}):
        with patch("temporalio.client.Client.connect", return_value=mock_client):
            result = asyncio.run(_mod["dispatch_all"]())

    assert result == 1
    # dispatch_all starts workflows but does NOT mark done — that happens in collect_results
    mock_client.start_workflow.assert_called_once()


def test_dispatch_all_multiple_tasks(tmp_path):
    """dispatch_all starts multiple workflows for multiple pending tasks."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-a1] --provider zhipu --max-turns 20 "Fix one. Test: uv run pytest assays/test_one.py -x"`
        - [ ] `ribosome [t-b2] --provider volcano --max-turns 40 "Fix two. Test: uv run pytest assays/test_two.py -x"`
    """),
    )

    mock_client = AsyncMock()
    mock_handle = MagicMock()
    mock_client.start_workflow = AsyncMock(return_value=mock_handle)
    mock_workflow_mod = MagicMock()

    with patch.dict("sys.modules", {"workflow": mock_workflow_mod}):
        with patch("temporalio.client.Client.connect", return_value=mock_client):
            result = asyncio.run(_mod["dispatch_all"]())

    assert result == 2
    assert mock_client.start_workflow.call_count == 2


# ── test gate tests ──────────────────────────────────────────────────


def test_dispatch_all_skips_no_test_ref(tmp_path, capsys):
    """Tasks without test file or spec reference are skipped by test gate."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-notest] --provider zhipu "Do something without tests"`
    """),
    )
    result = asyncio.run(_mod["dispatch_all"]())
    assert result == 0
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out
    assert "no test file or spec" in captured.out


def test_dispatch_all_spec_bypasses_test_gate(tmp_path):
    """Tasks referencing a spec file in loci/plans/ bypass the test gate."""
    qf = tmp_path / "translation-queue.md"
    _write_queue(
        qf,
        textwrap.dedent("""\
        - [ ] `ribosome [t-spec] --provider zhipu --max-turns 15 "Execute the spec at ~/germline/loci/plans/my-spec.md"`
    """),
    )

    mock_client = AsyncMock()
    mock_handle = MagicMock()
    mock_client.start_workflow = AsyncMock(return_value=mock_handle)
    mock_workflow_mod = MagicMock()

    with patch.dict("sys.modules", {"workflow": mock_workflow_mod}):
        with patch("temporalio.client.Client.connect", return_value=mock_client):
            result = asyncio.run(_mod["dispatch_all"]())

    assert result == 1
    mock_client.start_workflow.assert_called_once()


# ── log tests ─────────────────────────────────────────────────────────


def test_log_writes_to_file(tmp_path):
    """log() writes timestamped lines to LOG_FILE."""
    lfile = tmp_path / "dispatch.log"
    _mod["LOG_FILE"] = lfile
    log("test message")
    content = lfile.read_text()
    assert "test message" in content
    assert "[" in content  # timestamp present


def test_log_json_mode_suppresses_stdout(tmp_path, capsys):
    """In JSON mode, log does not print to stdout."""
    _mod["_json_mode"] = True
    try:
        log("json suppressed")
        captured = capsys.readouterr()
        assert "json suppressed" not in captured.out
    finally:
        _mod["_json_mode"] = False


# ── main / CLI tests ─────────────────────────────────────────────────


def test_main_help(capsys):
    """--help prints docstring and exits."""
    with pytest.raises(SystemExit) as exc_info, patch("sys.argv", ["dispatch.py", "--help"]):
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "temporal-dispatch" in captured.out


def test_main_status_json(tmp_path, capsys):
    """--status --json calls show_status with json_output=True."""
    mock_wf = MagicMock()
    mock_wf.id = "wf-1"
    mock_wf.status.name = "RUNNING"
    mock_wf.start_time = "2026-01-01"

    # list_workflows is used with `async for`, so return an async iterable
    async def _aiter_workflows(**kwargs):
        yield mock_wf

    mock_client = AsyncMock()
    mock_client.list_workflows = MagicMock(return_value=_aiter_workflows())

    with patch("temporalio.client.Client.connect", return_value=mock_client):
        with patch("sys.argv", ["dispatch.py", "--status", "--json"]):
            main()

    captured = capsys.readouterr()
    assert "wf-1" in captured.out


# ── poll_loop connection-failure Telegram alert tests ──────────────────


def test_conn_failure_telegram_alert():
    """Telegram alert fires after 5 consecutive OSError failures, and not
    again until the failure streak resets."""
    poll_loop = _mod["poll_loop"]

    call_count = 0

    async def _fake_dispatch():
        nonlocal call_count
        call_count += 1
        if call_count <= 5:
            raise OSError("connection refused")
        if call_count == 6:
            return 0  # success — resets streak
        if call_count <= 11:
            raise OSError("connection refused again")
        raise SystemExit(0)  # break the infinite loop

    async def _fake_collect():
        pass

    popen_calls: list[tuple[tuple, dict]] = []

    def _popen_side_effect(*args, **kwargs):
        popen_calls.append((args, kwargs))
        return MagicMock()

    orig_dispatch = _mod["dispatch_all"]
    orig_collect = _mod["collect_results"]
    _mod["dispatch_all"] = _fake_dispatch
    _mod["collect_results"] = _fake_collect

    try:
        with patch("subprocess.Popen", side_effect=_popen_side_effect):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with contextlib.suppress(SystemExit):
                    asyncio.run(poll_loop(interval=1))
    finally:
        _mod["dispatch_all"] = orig_dispatch
        _mod["collect_results"] = orig_collect

    # First streak: failures 1-4 → no alert, failure 5 → first alert
    # Cycle 6: success → streak resets
    # Second streak: failures 7-10 → no alert, failure 11 → second alert
    assert len(popen_calls) == 2, f"expected 2 Popen calls, got {len(popen_calls)}"
    for call_args, _call_kwargs in popen_calls:
        cmd = call_args[0]
        assert "python3" in cmd[0]
        assert "send_message" in cmd[2]
        assert "temporal-dispatch" in cmd[2]


# ── ribosome syntax pre-check tests ──────────────────────────────────────


def test_ribosome_syntax_precheck():
    """Syntax error in ribosome script causes early return without running ribosome."""
    worker_path = Path.home() / "germline/effectors/polysome/worker.py"
    source = worker_path.read_text()
    ns: dict = {"__name__": "worker_under_test", "__file__": str(worker_path)}
    exec(source, ns)

    translate = ns["translate"]
    worker_subprocess = ns["_subprocess"]

    # Mock _subprocess.run to return syntax error for bash -n
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stderr = "line 42: syntax error near unexpected token"

    with patch.object(worker_subprocess, "run", return_value=mock_result):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            result = asyncio.run(translate("test task [t-syn01]", "zhipu"))

    assert result["exit_code"] == -1
    assert result["success"] is False
    assert "ribosome script has syntax error" in result["stderr"]
    assert "syntax error near unexpected token" in result["stderr"]
    # Ribosome subprocess must NOT have been launched
    mock_exec.assert_not_called()
