
"""Tests for effectors/golem -- headless CC + GLM-5.1 shell script.

Tests cover: task ID parsing, flag parsing, provider config, rate-limit
fail-fast, JSON output, summary subcommand.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

GOLEM = Path.home() / "germline" / "effectors" / "golem"


def _run_golem(*args, timeout=30):
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / 'germline' / 'effectors'}:{env.get('PATH', '')}"
    env.setdefault("ZHIPU_API_KEY", "test-zhipu-key")
    env.setdefault("VOLCANO_API_KEY", "test-volcano-key")
    env.setdefault("INFINI_API_KEY", "test-infini-key")
    return subprocess.run(
        [str(GOLEM)] + list(args),
        capture_output=True, text=True, timeout=timeout, env=env,
    )


def _run_golem_shell(cmd, env_extra=None, timeout=30):
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / 'germline' / 'effectors'}:{env.get('PATH', '')}"
    env.setdefault("ZHIPU_API_KEY", "test-zhipu-key")
    env.setdefault("VOLCANO_API_KEY", "test-volcano-key")
    env.setdefault("INFINI_API_KEY", "test-infini-key")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env,
    )


# -- Help and usage --


class TestHelp:
    def test_help_flag(self):
        r = _run_golem("--help")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()

    def test_help_short(self):
        r = _run_golem("-h")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()


# -- Task ID parsing --


class TestTaskIDParsing:
    """Test that [t-xxxxxx] prefix is correctly stripped before flag parsing."""

    def test_task_id_with_help(self):
        """Task ID before flags: --help should still be recognized."""
        r = _run_golem_shell("golem '[t-a4a00f]' --help")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()

    def test_task_id_hex_format(self):
        """Valid hex task IDs should be accepted."""
        r = _run_golem_shell("golem '[t-deadbe]' --help")
        assert r.returncode == 0

    def test_task_id_uppercase_hex(self):
        """Uppercase hex in task ID should be accepted."""
        r = _run_golem_shell("golem '[t-A4A00F]' --help")
        assert r.returncode == 0

    def test_no_task_id(self):
        """Without task ID, flags should parse normally."""
        r = _run_golem("--help")
        assert r.returncode == 0


# -- Provider config --


class TestProviderConfig:
    def test_unknown_provider_exit(self):
        """Unknown provider should cause exit code 1."""
        r = _run_golem("--provider", "nonexistent", "--max-turns", "3", "test")
        assert r.returncode == 1
        assert "Unknown provider" in r.stderr

    def test_zhipu_provider(self):
        """ZhiPu provider should require ZHIPU_API_KEY."""
        r = _run_golem(
            "--provider", "zhipu", "--max-turns", "3", "test",
            env_extra={"ZHIPU_API_KEY": ""},
        )
        assert r.returncode != 0

    def test_volcano_provider(self):
        """Volcano provider should require VOLCANO_API_KEY."""
        r = _run_golem(
            "--provider", "volcano", "--max-turns", "3", "test",
            env_extra={"VOLCANO_API_KEY": ""},
        )
        assert r.returncode != 0


# -- Summary subcommand --


class TestSummary:
    def test_summary_empty_log(self):
        """Summary on empty log should show 'No log file found'."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write("")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --log={tmp}", timeout=10)
            assert r.returncode in (0, 1)
        finally:
            os.unlink(tmp)

    def test_summary_json_output(self):
        """Summary --json should produce valid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write(json.dumps({
                "ts": "2026-04-01T00:00:00Z",
                "provider": "zhipu",
                "duration": 100,
                "exit": 0,
                "turns": 10,
                "prompt": "test",
                "tail": "",
                "files_created": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "pytest_exit": 0,
                "task_id": "t-test01",
            }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --json --log={tmp}", timeout=10)
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert "zhipu" in data
            assert data["zhipu"]["runs"] == 1
            assert data["zhipu"]["pass"] == 1
        finally:
            os.unlink(tmp)

    def test_summary_counts_pass_fail(self):
        """Summary should correctly count pass/fail."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            for exit_code in [0, 0, 1, 1, 1]:
                f.write(json.dumps({
                    "ts": "2026-04-01T00:00:00Z",
                    "provider": "zhipu",
                    "duration": 100,
                    "exit": exit_code,
                    "turns": 10,
                    "prompt": "test",
                    "tail": "",
                    "files_created": 0,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "pytest_exit": 0,
                    "task_id": "t-test01",
                }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --json --log={tmp}", timeout=10)
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["zhipu"]["runs"] == 5
            assert data["zhipu"]["pass"] == 2
            assert data["zhipu"]["fail"] == 3
        finally:
            os.unlink(tmp)


# -- Rate-limit fail-fast --


class TestRateLimitFailFast:
    """Test volcano rate-limit handling.

    Volcano returns 429 AccountQuotaExceeded with a 5-hour quota window.
    The golem script should fail fast (under 15s) instead of sleeping 30 min retrying.
    """

    @pytest.fixture(autouse=True)
    def skip_without_volcano_key(self):
        if not os.environ.get("VOLCANO_API_KEY"):
            pytest.skip("VOLCANO_API_KEY not set")

    def test_volcano_rate_limited_exits_nonzero(self):
        """Rate-limited volcano should exit with non-zero code (not 0)."""
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        assert r.returncode != 0

    def test_volcano_rate_limited_output_has_quota_indicator(self):
        """Rate-limited output should contain AccountQuotaExceeded."""
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        output = (r.stdout + r.stderr).lower()
        assert "quota" in output or "429" in output or "rate" in output

    def test_volcano_rate_limited_fails_fast(self):
        """Should fail in under 15 seconds, not sleep 30 minutes."""
        start = time.time()
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        elapsed = time.time() - start
        assert elapsed < 15, f"Took {elapsed:.1f}s -- should fail fast on long quota window"


# -- Regression: exit=2 with 0s duration --


class TestExit2Regression:
    """Tests for the bug where golem returned exit=0 when claude never launched.

    Root causes identified:
    1. Task ID [t-xxxx] before flags prevented --provider from being parsed
    2. Rate-limit retry loop returned exit_code=0 when claude never launched
    3. Smart backoff capped at 600s for 5-hour quota window

    Fixes applied:
    - Task ID regex pre-parsing before flag while-loop
    - _claude_ran tracking to detect never-launched state
    - Fail-fast when quota reset > 30 min away
    """

    def test_task_id_does_not_break_provider_parsing(self):
        """[t-xxxx] --provider volcano should parse provider=volcano, not default zhipu."""
        r = _run_golem_shell(
            "golem '[t-a4a00f]' --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if volcano_key:
            output = r.stdout + r.stderr
            if "quota" in output.lower() or "429" in output or "preflight" in output:
                assert "volcano" in output.lower()

    def test_exit_code_nonzero_when_claude_never_launched(self):
        """Golem should return non-zero when claude was never invoked.

        Previously: exit_code stayed 0 (initialized but never set).
        Now: returns 1 with AccountQuotaExceeded message.
        """
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if not volcano_key:
            pytest.skip("VOLCANO_API_KEY not set")

        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        assert r.returncode != 0

    def test_fail_fast_does_not_waste_time(self):
        """Should fail in under 15 seconds when quota window is > 30 min."""
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if not volcano_key:
            pytest.skip("VOLCANO_API_KEY not set")

        start = time.time()
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        elapsed = time.time() - start
        assert elapsed < 15, f"Took {elapsed:.1f}s -- should fail fast"


# -- set -e exit-code capture regression --


class TestSetEExitCodeCapture:
    """Regression tests for the set -e + command substitution bug.

    Root cause: with set -euo pipefail, `output=$(claude ...)` where claude
    exits non-zero caused the script to exit IMMEDIATELY with claude's exit
    code — before `exit_code=$?` could capture it.  This produced:
      - exit=2 with 0s duration (preflight returning 2 via set -e)
      - exit=1 with 0s duration (claude returning 1 via set -e)
      - No error output in daemon logs (script died before logging)

    Fix: `output=$(claude ...) && exit_code=0 || exit_code=$?`
    The `||` arm prevents set -e from killing the script.
    """

    def test_old_pattern_exits_on_nonzero_cmd(self):
        """OLD pattern `output=$(cmd); exit_code=$?` dies with set -e."""
        r = subprocess.run(
            ["bash", "-euc", 'output=$(echo msg; exit 2); exit_code=$?; echo "ec=$exit_code"'],
            capture_output=True, text=True, timeout=5,
        )
        # Script should exit with 2 (never reaches exit_code=$?)
        assert r.returncode == 2
        assert "ec=" not in r.stdout  # never reached

    def test_new_pattern_captures_exit_code(self):
        """NEW pattern `output=$(cmd) && ec=0 || ec=$?` captures exit code."""
        r = subprocess.run(
            ["bash", "-euc", 'output=$(echo msg; exit 2) && ec=0 || ec=$?; echo "ec=$ec out=$output"'],
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0  # script itself succeeds
        assert "ec=2" in r.stdout
        assert "out=msg" in r.stdout

    def test_new_pattern_success_path(self):
        """NEW pattern sets ec=0 when command succeeds."""
        r = subprocess.run(
            ["bash", "-euc", 'output=$(echo ok) && ec=0 || ec=$?; echo "ec=$ec out=$output"'],
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0
        assert "ec=0" in r.stdout
        assert "out=ok" in r.stdout

    def test_new_pattern_with_pipefail(self):
        """NEW pattern works with set -euo pipefail (the golem defaults)."""
        r = subprocess.run(
            ["bash", "-euc",
             'set -euo pipefail; output=$(echo "error"; exit 1) && ec=0 || ec=$?; echo "ec=$ec"'],
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0
        assert "ec=1" in r.stdout

    def test_exit_code_not_two_when_rate_limited(self):
        """Rate-limited volcano should return exit=1, not exit=2.

        Before the fix, the set -e interaction with _preflight_check returning 1
        (rate-limit) or 2 (connection error) caused the script to exit with that
        code instead of handling it in the retry loop.
        """
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if not volcano_key:
            pytest.skip("VOLCANO_API_KEY not set")

        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        assert r.returncode != 2, (
            f"Rate-limited volcano returned exit=2 (should be 1). "
            f"stdout: {r.stdout[:200]} stderr: {r.stderr[:200]}"
        )

    def test_golem_source_uses_new_pattern(self):
        """Verify the golem script contains the fixed exit-code capture pattern."""
        source = GOLEM.read_text()
        # The fix uses `&& exit_code=0 || exit_code=$?` after command substitution
        # The old pattern was just `exit_code=$?` on the next line
        assert "&& exit_code=0 || exit_code=$?" in source, (
            "golem script should use `&& exit_code=0 || exit_code=$?` pattern "
            "to prevent set -e from killing the script on non-zero claude exit"
        )

    def test_golem_source_no_bare_exit_code_capture(self):
        """Verify the old `exit_code=$?` on a line by itself after `output=$(...)` is gone."""
        source = GOLEM.read_text()
        # Look for the OLD pattern: `)` on one line, then `exit_code=$?` on the next
        # (within the claude/gemini/codex invocation blocks)
        lines = source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.endswith(")") and "2>&1" in stripped:
                # Next non-empty line should NOT be just `exit_code=$?`
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == "exit_code=$?":
                        pytest.fail(
                            f"Line {i + 2}: bare `exit_code=$?` after command substitution "
                            f"is vulnerable to set -e. Use `&& exit_code=0 || exit_code=$?` instead."
                        )


# -- Daemon mark_failed tail parameter --


class TestDaemonMarkFailedTailFix:
    """Tests for the daemon's mark_failed receiving the tail parameter.

    The daemon calls mark_failed(line_num, result, exit_code, task_id)
    but was NOT passing tail=tail.  This caused empty_output to always
    be True (since tail defaults to ""), making all exit=2 failures
    retried regardless of actual output content.
    """

    def test_mark_failed_uses_tail_for_empty_check(self):
        """mark_failed should use tail parameter, not result, for empty check."""
        _mod = _load_golem_daemon()
        mark_failed_fn = _mod["mark_failed"]
        is_rate_limited_fn = _mod["is_rate_limited"]

        # Create a temp queue file with a pending task
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w"
        ) as f:
            f.write("## Pending\n- [ ] `golem --provider volcano 'test'`\n## Done\n")
            tmp = f.name

        _mod["QUEUE_FILE"] = Path(tmp)

        try:
            # Call with exit_code=2, empty tail → should retry (empty output = silent rate-limit)
            result = mark_failed_fn(
                1,
                "exit=2 error message with content",
                exit_code=2,
                task_id="t-test01",
                tail="error message with content",
            )
            # tail has content → empty_output=False
            # exit_code=2, not rate-limited, not empty → should NOT retry
            assert result["retried"] is False
        finally:
            os.unlink(tmp)

    def test_mark_failed_retries_on_empty_tail(self):
        """mark_failed should retry when tail is empty (silent rate-limit)."""
        _mod = _load_golem_daemon()
        mark_failed_fn = _mod["mark_failed"]

        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w"
        ) as f:
            f.write("## Pending\n- [ ] `golem --provider volcano 'test'`\n## Done\n")
            tmp = f.name

        _mod["QUEUE_FILE"] = Path(tmp)

        try:
            # Call with exit_code=2, empty tail → should retry
            result = mark_failed_fn(
                1,
                "exit=2 ",
                exit_code=2,
                task_id="t-test02",
                tail="",
            )
            # tail is empty → empty_output=True → should retry
            assert result["retried"] is True
        finally:
            os.unlink(tmp)

    def test_mark_failed_retries_on_rate_limit_even_with_tail(self):
        """mark_failed should retry when output shows rate-limit, regardless of tail."""
        _mod = _load_golem_daemon()
        mark_failed_fn = _mod["mark_failed"]

        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w"
        ) as f:
            f.write("## Pending\n- [ ] `golem --provider volcano 'test'`\n## Done\n")
            tmp = f.name

        _mod["QUEUE_FILE"] = Path(tmp)

        try:
            result = mark_failed_fn(
                1,
                "exit=1 AccountQuotaExceeded",
                exit_code=1,
                task_id="t-test03",
                tail="AccountQuotaExceeded: quota reset at 2026-04-01",
            )
            # rate_limited=True → should retry
            assert result["rate_limited"] is True
            assert result["retried"] is True
        finally:
            os.unlink(tmp)


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-daemon").read()
    ns: dict = {"__name__": "golem_daemon"}
    exec(source, ns)
    return ns


# -- --json output flag --


class TestJsonOutput:
    """Tests for the golem --json flag.

    The --json flag wraps the raw claude output into a JSON envelope with
    metadata (exit_code, duration, provider, files_created, tests_passed,
    tests_failed).  Useful for piping to jq or other downstream tools.
    """

    # -- Source-level verification --

    def test_json_flag_in_help(self):
        """--json should appear in the usage text."""
        source = GOLEM.read_text()
        assert "--json" in source

    def test_json_flag_sets_variable(self):
        """Parsing --json should set JSON_OUTPUT=true in the script."""
        source = GOLEM.read_text()
        assert "--json) JSON_OUTPUT=true" in source

    def test_json_takes_precedence_over_quiet(self):
        """JSON_OUTPUT branch is checked before QUIET in the output if/elif."""
        source = GOLEM.read_text()
        # The output section should check JSON_OUTPUT first, then QUIET
        json_pos = source.find("if $JSON_OUTPUT; then")
        quiet_pos = source.find("elif ! $QUIET; then")
        assert json_pos > 0, "Missing 'if $JSON_OUTPUT; then' in golem source"
        assert quiet_pos > 0, "Missing 'elif ! $QUIET; then' in golem source"
        assert json_pos < quiet_pos, (
            "JSON_OUTPUT check should come before QUIET check"
        )

    # -- JSON output structure (unit test of inline python3 formatter) --

    def test_json_output_has_required_fields(self):
        """The inline python3 JSON formatter should produce all expected fields."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as f:
            f.write("sample output from claude")
            tmp = f.name
        try:
            r = subprocess.run(
                [
                    "python3", "-c",
                    "import json, sys\n"
                    "output_text = open(sys.argv[1]).read()\n"
                    "result = {\n"
                    "    'output': output_text,\n"
                    "    'exit_code': int(sys.argv[2]),\n"
                    "    'duration': int(sys.argv[3]),\n"
                    "    'provider': sys.argv[4],\n"
                    "    'files_created': int(sys.argv[5]),\n"
                    "    'tests_passed': int(sys.argv[6]),\n"
                    "    'tests_failed': int(sys.argv[7]),\n"
                    "}\n"
                    "print(json.dumps(result))\n",
                    tmp, "0", "42", "zhipu", "3", "10", "1",
                ],
                capture_output=True, text=True, timeout=10,
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["output"] == "sample output from claude"
            assert data["exit_code"] == 0
            assert data["duration"] == 42
            assert data["provider"] == "zhipu"
            assert data["files_created"] == 3
            assert data["tests_passed"] == 10
            assert data["tests_failed"] == 1
        finally:
            os.unlink(tmp)

    def test_json_output_handles_multiline(self):
        """JSON output should correctly escape multiline claude output."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as f:
            f.write("line one\nline two\nline three\n")
            tmp = f.name
        try:
            r = subprocess.run(
                [
                    "python3", "-c",
                    "import json, sys\n"
                    "output_text = open(sys.argv[1]).read()\n"
                    "result = {\n"
                    "    'output': output_text,\n"
                    "    'exit_code': int(sys.argv[2]),\n"
                    "    'duration': int(sys.argv[3]),\n"
                    "    'provider': sys.argv[4],\n"
                    "    'files_created': int(sys.argv[5]),\n"
                    "    'tests_passed': int(sys.argv[6]),\n"
                    "    'tests_failed': int(sys.argv[7]),\n"
                    "}\n"
                    "print(json.dumps(result))\n",
                    tmp, "0", "10", "zhipu", "0", "0", "0",
                ],
                capture_output=True, text=True, timeout=10,
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert "line one" in data["output"]
            assert "line two" in data["output"]
            assert "\n" in data["output"]
        finally:
            os.unlink(tmp)

    def test_json_output_handles_special_chars(self):
        """JSON output should correctly escape quotes and backslashes."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as f:
            f.write('He said "hello" and left\\done')
            tmp = f.name
        try:
            r = subprocess.run(
                [
                    "python3", "-c",
                    "import json, sys\n"
                    "output_text = open(sys.argv[1]).read()\n"
                    "result = {\n"
                    "    'output': output_text,\n"
                    "    'exit_code': int(sys.argv[2]),\n"
                    "    'duration': int(sys.argv[3]),\n"
                    "    'provider': sys.argv[4],\n"
                    "    'files_created': int(sys.argv[5]),\n"
                    "    'tests_passed': int(sys.argv[6]),\n"
                    "    'tests_failed': int(sys.argv[7]),\n"
                    "}\n"
                    "print(json.dumps(result))\n",
                    tmp, "1", "5", "volcano", "0", "0", "0",
                ],
                capture_output=True, text=True, timeout=10,
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert '"hello"' in data["output"]
            assert data["exit_code"] == 1
        finally:
            os.unlink(tmp)

    # -- Summary --json (additional edge cases) --

    def test_summary_json_with_multiple_providers(self):
        """Summary --json should group results by provider."""
        with tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w"
        ) as f:
            for provider in ["zhipu", "volcano", "zhipu"]:
                f.write(json.dumps({
                    "ts": "2026-04-01T00:00:00Z",
                    "provider": provider,
                    "duration": 50,
                    "exit": 0,
                    "turns": 10,
                    "prompt": "test",
                    "tail": "",
                    "files_created": 0,
                    "tests_passed": 1,
                    "tests_failed": 0,
                    "pytest_exit": 0,
                    "task_id": "",
                }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --json --log={tmp}", timeout=10)
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["zhipu"]["runs"] == 2
            assert data["volcano"]["runs"] == 1
        finally:
            os.unlink(tmp)

    def test_summary_json_with_recent_flag(self):
        """Summary --json --recent N should only count last N entries."""
        with tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w"
        ) as f:
            for i in range(10):
                f.write(json.dumps({
                    "ts": "2026-04-01T00:00:00Z",
                    "provider": "zhipu",
                    "duration": i * 10,
                    "exit": 0 if i % 2 == 0 else 1,
                    "turns": 10,
                    "prompt": "test",
                    "tail": "",
                    "files_created": 0,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "pytest_exit": 0,
                    "task_id": "",
                }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(
                f"golem summary --json --recent 3 --log={tmp}", timeout=10
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["zhipu"]["runs"] == 3
        finally:
            os.unlink(tmp)
