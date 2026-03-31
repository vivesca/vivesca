#!/usr/bin/env python3
"""Tests for effectors/browse — web content extractor with fallback chain.

browse is a script (effectors/browse), not an importable module.
It is loaded via exec() into isolated namespaces.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BROWSE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "browse"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def ns():
    """Load browse via exec into an isolated namespace dict."""
    ns_dict: dict = {"__name__": "test_browse", "__file__": str(BROWSE_PATH)}
    source = BROWSE_PATH.read_text(encoding="utf-8")
    exec(source, ns_dict)
    return ns_dict


# ── File structure tests ───────────────────────────────────────────────────


class TestBrowseBasics:
    def test_file_exists(self):
        """Test that browse effector file exists."""
        assert BROWSE_PATH.exists()
        assert BROWSE_PATH.is_file()

    def test_is_python_script(self):
        """Test that browse has Python shebang."""
        first_line = BROWSE_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        """Test that browse has docstring."""
        content = BROWSE_PATH.read_text()
        assert '"""' in content

    def test_docstring_mentions_fallback(self):
        """Test docstring mentions fallback chain."""
        content = BROWSE_PATH.read_text()
        assert "fallback" in content.lower()

    def test_docstring_mentions_needs_browser(self):
        """Test docstring mentions NEEDS_BROWSER."""
        content = BROWSE_PATH.read_text()
        assert "NEEDS_BROWSER" in content


# ── run_command() helper ───────────────────────────────────────────────────


class TestRunCommand:
    def test_returns_stdout_on_success(self, ns, monkeypatch):
        """Should return stripped stdout on success."""
        mock_result = MagicMock(stdout="  content  \n")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        assert ns["run_command"](["cmd"]) == "content"

    def test_returns_none_on_empty_output(self, ns, monkeypatch):
        """Should return None when command output is empty."""
        mock_result = MagicMock(stdout="   \n")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        assert ns["run_command"](["cmd"]) is None

    def test_returns_none_on_failure(self, ns, monkeypatch):
        """Should return None on CalledProcessError."""
        monkeypatch.setattr(
            subprocess, "run",
            MagicMock(side_effect=subprocess.CalledProcessError(1, "cmd")),
        )
        assert ns["run_command"](["cmd"]) is None

    def test_returns_none_on_generic_exception(self, ns, monkeypatch):
        """Should return None on any exception."""
        monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=OSError("fail")))
        assert ns["run_command"](["cmd"]) is None

    def test_uses_check_true(self, ns, monkeypatch):
        """Should call subprocess.run with check=True."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        ns["run_command"](["cmd"])
        assert calls[0].get("check") is True

    def test_captures_output_and_text(self, ns, monkeypatch):
        """Should capture stdout/stderr and use text mode."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        ns["run_command"](["cmd"])
        assert calls[0].get("capture_output") is True
        assert calls[0].get("text") is True


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_exits(self, ns, monkeypatch):
        """Should exit 1 when no URL provided."""
        monkeypatch.setattr(sys, "argv", ["browse"])
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 1

    def test_too_many_args_exits(self, ns, monkeypatch):
        """Should exit 1 when too many args provided."""
        monkeypatch.setattr(sys, "argv", ["browse", "url1", "url2"])
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 1

    def test_defuddle_success(self, ns, capsys, monkeypatch):
        """Should print defuddle output and exit 0."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        ns["run_command"] = lambda cmd: "markdown content" if cmd[0] == "defuddle" else None
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert out.strip() == "markdown content"

    def test_curl_html2text_fallback(self, ns, capsys, monkeypatch):
        """Should use curl+html2text when defuddle returns nothing."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])

        def mock_run_command(cmd):
            if cmd[0] == "defuddle":
                return None
            if cmd[0] == "curl":
                return "<html><body>Hello</body></html>"
            return None

        ns["run_command"] = mock_run_command

        # Mock subprocess.run for the html2text call in main()
        mock_h2t = MagicMock(stdout="Hello\n", returncode=0)
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_h2t)

        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "Hello" in out

    def test_needs_browser_when_all_fail(self, ns, capsys, monkeypatch):
        """Should print NEEDS_BROWSER and exit 1 when all methods fail."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        ns["run_command"] = lambda cmd: None
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "NEEDS_BROWSER" in out

    def test_curl_fails_html2text_not_called(self, ns, capsys, monkeypatch):
        """Should skip html2text when curl returns nothing."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        run_cmd_calls = []
        def mock_run_command(cmd):
            run_cmd_calls.append(cmd)
            return None
        ns["run_command"] = mock_run_command
        subproc_calls = []
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: (subproc_calls.append(a), MagicMock())[1],
        )
        with pytest.raises(SystemExit):
            ns["main"]()
        # html2text should not be called via subprocess.run since curl returned None
        assert not any("html2text" in str(c) for c in subproc_calls)

    def test_defuddle_has_priority(self, ns, capsys, monkeypatch):
        """Defuddle output should be used when available (no curl fallback)."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        call_log = []
        def mock_run_command(cmd):
            call_log.append(cmd[0])
            if cmd[0] == "defuddle":
                return "defuddle content"
            return None
        ns["run_command"] = mock_run_command
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "defuddle content" in out
        # curl should not have been called
        assert "curl" not in call_log

    def test_exits_zero_on_success(self, ns, capsys, monkeypatch):
        """Should exit 0 when content extracted successfully."""
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        ns["run_command"] = lambda cmd: "content" if cmd[0] == "defuddle" else None
        with pytest.raises(SystemExit) as exc_info:
            ns["main"]()
        assert exc_info.value.code == 0


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_exits_nonzero(self):
        """Running browse with no args should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(BROWSE_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0

    def test_no_args_shows_usage(self):
        """Running browse with no args should show docstring/usage."""
        r = subprocess.run(
            [sys.executable, str(BROWSE_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        output = r.stdout + r.stderr
        assert "browse" in output.lower() or "URL" in output

    def test_file_is_executable(self):
        """Test browse file has execute permission."""
        assert BROWSE_PATH.stat().st_mode & 0o111
