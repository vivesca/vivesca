"""Tests for ribosome-daemon early-kill on rate-limit detection.

Spec: When a ribosome subprocess outputs a rate-limit pattern within its first
60 seconds, the daemon should kill the subprocess immediately instead of
waiting for the full 30-minute timeout. This saves slots and triggers
provider cooldown faster.

Implementation requirement:
- run_ribosome() must use subprocess.Popen instead of subprocess.run
- Poll stdout/stderr periodically (every 2s) during the first 60s
- If RATE_LIMIT_PATTERNS matches accumulated output, send SIGTERM to
  the process group, wait 5s, then SIGKILL if still alive
- Return exit_code=143 (SIGTERM), tail containing the rate-limit output,
  and actual duration (not timeout duration)
- After 60s, stop polling and just wait for completion as before
- Must not affect tasks that don't hit rate limits
"""

import time
from pathlib import Path


def _load_ribosome_daemon():
    """Load the ribosome-daemon module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/ribosome-daemon")).read()
    ns: dict = {"__name__": "ribosome_daemon"}
    exec(source, ns)
    return ns


_mod = _load_ribosome_daemon()
_orig_run_ribosome = _mod["run_ribosome"]
_orig_extract = _mod["_extract_task_id"]
_orig_log = _mod["log"]


def _run(cmd: str, task_id: str = "t-test00") -> tuple[str, int, str, int]:
    """Run a command through run_ribosome with test patches."""
    # Patch _extract_task_id and log inside the module namespace
    old_extract = _mod["_extract_task_id"]
    old_log = _mod["log"]
    _mod["_extract_task_id"] = lambda c: task_id
    _mod["log"] = lambda *a, **kw: None
    try:
        return _mod["run_ribosome"](cmd)
    finally:
        _mod["_extract_task_id"] = old_extract
        _mod["log"] = old_log


class TestEarlyKillRateLimit:
    """run_ribosome must kill subprocesses that emit rate-limit patterns early."""

    def test_rate_limit_killed_within_10s(self):
        """A process that prints a 429 error should be killed quickly, not after 30min."""
        cmd = (
            'python3 -c "'
            "import time, sys; "
            "time.sleep(1); "
            "print('Error: 429 Too Many Requests - rate limit exceeded'); "
            "sys.stdout.flush(); "
            'time.sleep(3600)"'
        )

        start = time.time()
        _, exit_code, tail, _ = _run(cmd, "t-test01")
        elapsed = time.time() - start

        # Must complete in under 15s, not 1800s
        assert elapsed < 15, f"Early kill took {elapsed:.1f}s — should be <15s"
        assert exit_code != 0
        assert exit_code != 124, "Should not reach timeout"
        assert "429" in tail

    def test_rate_limit_pattern_AccountQuotaExceeded(self):
        """AccountQuotaExceeded pattern should also trigger early kill."""
        cmd = (
            'python3 -c "'
            "import time, sys; "
            "print('AccountQuotaExceeded: please retry later'); "
            "sys.stdout.flush(); "
            'time.sleep(3600)"'
        )

        start = time.time()
        _, exit_code, tail, _ = _run(cmd, "t-test02")
        elapsed = time.time() - start

        assert elapsed < 15
        assert exit_code != 0
        assert "AccountQuotaExceeded" in tail

    def test_normal_task_not_killed(self):
        """A task that produces normal output should NOT be killed early."""
        cmd = (
            'python3 -c "'
            "import sys; "
            "print('Working on pyright fixes...'); "
            "print('Fixed 3 type errors'); "
            'sys.exit(0)"'
        )

        _, exit_code, tail, _ = _run(cmd, "t-test03")

        assert exit_code == 0
        assert "Fixed 3 type errors" in tail

    def test_empty_output_fast_exit_still_works(self):
        """Empty stdout + fast exit (existing pattern) still works."""
        cmd = 'python3 -c "import sys; sys.exit(1)"'

        _, exit_code, _tail, _ = _run(cmd, "t-test04")

        assert exit_code == 1

    def test_return_type_unchanged(self):
        """run_ribosome must still return (cmd, exit_code, tail, duration) tuple."""
        cmd = 'echo "done"'

        result = _run(cmd, "t-test05")

        assert isinstance(result, tuple)
        assert len(result) == 4
        returned_cmd, exit_code, tail, duration = result
        assert isinstance(returned_cmd, str)
        assert isinstance(exit_code, int)
        assert isinstance(tail, str)
        assert isinstance(duration, int)

    def test_too_many_requests_pattern(self):
        """'too many requests' (case-insensitive) triggers early kill."""
        cmd = (
            'python3 -c "'
            "import time, sys; "
            "print('Too Many Requests for model'); "
            "sys.stdout.flush(); "
            'time.sleep(3600)"'
        )

        start = time.time()
        _, exit_code, _tail, _ = _run(cmd, "t-test06")
        elapsed = time.time() - start

        assert elapsed < 15
        assert exit_code != 0
