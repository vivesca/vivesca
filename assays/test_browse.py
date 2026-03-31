"""Tests for effectors/browse — web content extractor with fallback chain."""

from __future__ import annotations

import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BROWSE_PATH = Path(__file__).resolve().parent.parent / "effectors" / "browse"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_browse_ns():
    """Load the browse effector into an isolated namespace."""
    ns = {
        "__name__": "browse_test",
        "__file__": str(BROWSE_PATH),
    }
    exec(open(BROWSE_PATH).read(), ns)  # noqa: S102
    return ns


def _successful_run(stdout: str, returncode: int = 0):
    """Build a mock subprocess.run result that succeeded."""
    result = MagicMock()
    result.stdout = stdout
    result.stderr = ""
    result.returncode = returncode
    return result


def _failed_run(side_effect=None):
    """Build a mock subprocess.run that raises CalledProcessError."""
    if side_effect:
        return side_effect
    return subprocess.CalledProcessError(1, "cmd")


# ---------------------------------------------------------------------------
# Tests: run_command helper
# ---------------------------------------------------------------------------

class TestRunCommand:
    """Unit tests for the run_command helper function."""

    def test_returns_stripped_stdout(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]
        with patch("subprocess.run", return_value=_successful_run("  hello world  \n")):
            assert run_cmd(["echo", "hi"]) == "hello world"

    def test_returns_none_on_empty_stdout(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]
        with patch("subprocess.run", return_value=_successful_run("   \n")):
            assert run_cmd(["echo", ""]) is None

    def test_returns_none_on_called_process_error(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
            assert run_cmd(["false"]) is None

    def test_returns_none_on_generic_exception(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]
        with patch("subprocess.run", side_effect=OSError("boom")):
            assert run_cmd(["bad"]) is None


# ---------------------------------------------------------------------------
# Tests: CLI argument handling
# ---------------------------------------------------------------------------

class TestCLIArgs:
    """Tests for argument parsing and help output."""

    def test_no_args_prints_doc_and_exits_1(self, capsys):
        ns = _load_browse_ns()
        main = ns["main"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage: browse URL" in captured.out

    def test_help_flag_exits_0(self, capsys):
        ns = _load_browse_ns()
        main = ns["main"]
        # Patch sys.argv inside the namespace so main() sees --help
        ns["sys"].argv = ["browse", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Usage: browse URL" in captured.out

    def test_h_flag_exits_0(self, capsys):
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "-h"]
        main = ns["main"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_too_many_args_exits_1(self, capsys):
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "url1", "url2"]
        main = ns["main"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Tests: fallback chain
# ---------------------------------------------------------------------------

class TestFallbackChain:
    """Tests for the defuddle → curl+html2text → NEEDS_BROWSER chain."""

    def _run_main_with_url(self, url: str = "https://example.com", capsys=None):
        """Load browse, set argv, run main, return (stdout, exit_code)."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", url]
        main = ns["main"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        captured = capsys.readouterr() if capsys else None
        return captured, exc_info.value.code, ns

    def test_defuddle_succeeds_prints_output(self, capsys):
        """Step 1: defuddle returns content → printed, exit 0."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                return _successful_run("# My Page\nContent here")
            # Should not reach curl, but just in case
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        assert "# My Page" in output

    def test_defuddle_empty_curl_html2text_succeeds(self, capsys):
        """Step 2: defuddle empty → curl + html2text returns content → exit 0."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        call_count = {"n": 0}

        def mock_run(cmd, **kwargs):
            call_count["n"] += 1
            if cmd[0] == "defuddle":
                return _successful_run("")  # empty output
            if cmd[0] == "curl":
                return _successful_run("<html><body>Hello</body></html>")
            if cmd[0] == "html2text":
                return _successful_run("Hello from html2text")
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        assert "Hello from html2text" in output
        # Ensure defuddle was tried first
        assert call_count["n"] >= 2

    def test_both_fail_prints_needs_browser(self, capsys):
        """Step 3: defuddle + curl both fail → NEEDS_BROWSER, exit 1."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "NEEDS_BROWSER" in output

    def test_defuddle_fails_curl_succeeds_html2text_empty(self, capsys):
        """defuddle fails, curl works, html2text returns empty → NEEDS_BROWSER."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                raise subprocess.CalledProcessError(1, "defuddle")
            if cmd[0] == "curl":
                return _successful_run("<html></html>")
            if cmd[0] == "html2text":
                return _successful_run("   ")  # whitespace-only
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "NEEDS_BROWSER" in output

    def test_defuddle_fails_curl_fails_html2text_unreachable(self, capsys):
        """defuddle fails, curl returns empty → skip html2text → NEEDS_BROWSER."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        html2text_called = []

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                raise subprocess.CalledProcessError(1, "defuddle")
            if cmd[0] == "curl":
                return _successful_run("")  # empty html
            if cmd[0] == "html2text":
                html2text_called.append(True)
                return _successful_run("")
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "NEEDS_BROWSER" in output
        # html2text should never be called if curl returned nothing
        assert html2text_called == []

    def test_defuddle_empty_curl_succeeds_html2text_raises(self, capsys):
        """defuddle empty, curl works, html2text raises → NEEDS_BROWSER."""
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                return _successful_run("")
            if cmd[0] == "curl":
                return _successful_run("<html>stuff</html>")
            if cmd[0] == "html2text":
                raise subprocess.CalledProcessError(1, "html2text")
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "NEEDS_BROWSER" in output


# ---------------------------------------------------------------------------
# Tests: subprocess invocation
# ---------------------------------------------------------------------------

class TestSubprocessCalls:
    """Verify that subprocess.run is called with the right arguments."""

    def test_defuddle_called_with_url(self):
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com/page"]
        main = ns["main"]

        with patch("subprocess.run", return_value=_successful_run("ok")) as mock_run:
            with pytest.raises(SystemExit):
                main()

        first_call = mock_run.call_args_list[0]
        assert first_call[0][0] == ["defuddle", "parse", "https://example.com/page", "--md"]

    def test_curl_called_with_url(self):
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com/page"]
        main = ns["main"]

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                return _successful_run("")
            if cmd[0] == "curl":
                return _successful_run("")
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run) as mock_run_spy:
            with pytest.raises(SystemExit):
                main()

        curl_calls = [c for c in mock_run_spy.call_args_list if c[0][0][0] == "curl"]
        assert len(curl_calls) == 1
        assert curl_calls[0][0][0] == ["curl", "-sL", "https://example.com/page"]

    def test_html2text_receives_html_via_stdin(self):
        ns = _load_browse_ns()
        ns["sys"].argv = ["browse", "https://example.com"]
        main = ns["main"]

        def mock_run(cmd, **kwargs):
            if cmd[0] == "defuddle":
                return _successful_run("")
            if cmd[0] == "curl":
                return _successful_run("<html><body>Hi</body></html>")
            if cmd[0] == "html2text":
                # Verify html was passed via stdin
                assert kwargs.get("input") == "<html><body>Hi</body></html>"
                return _successful_run("Hi")
            return _successful_run("")

        with patch("subprocess.run", side_effect=mock_run):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Tests: subprocess.run parameters
# ---------------------------------------------------------------------------

class TestRunCommandParams:
    """Verify subprocess.run is called with proper parameters."""

    def test_run_command_uses_timeout(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]

        with patch("subprocess.run", return_value=_successful_run("ok")) as mock:
            run_cmd(["echo", "hi"])
            _, kwargs = mock.call_args
            assert kwargs.get("timeout") == 60

    def test_run_command_uses_text_mode(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]

        with patch("subprocess.run", return_value=_successful_run("ok")) as mock:
            run_cmd(["echo", "hi"])
            _, kwargs = mock.call_args
            assert kwargs.get("text") is True

    def test_run_command_captures_output(self):
        ns = _load_browse_ns()
        run_cmd = ns["run_command"]

        with patch("subprocess.run", return_value=_successful_run("ok")) as mock:
            run_cmd(["echo", "hi"])
            _, kwargs = mock.call_args
            assert kwargs.get("capture_output") is True
