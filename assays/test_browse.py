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
def browse():
    """Load browse via exec into an isolated namespace."""
    ns: dict = {"__name__": "test_browse", "__file__": str(BROWSE_PATH)}
    source = BROWSE_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("browse", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    mod._ns = ns  # keep reference to exec namespace for patching
    return mod


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
    def test_returns_stdout_on_success(self, browse, monkeypatch):
        """Should return stripped stdout on success."""
        mock_result = MagicMock(stdout="  content  \n")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        assert browse.run_command(["cmd"]) == "content"

    def test_returns_none_on_empty_output(self, browse, monkeypatch):
        """Should return None when command output is empty."""
        mock_result = MagicMock(stdout="   \n")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        assert browse.run_command(["cmd"]) is None

    def test_returns_none_on_failure(self, browse, monkeypatch):
        """Should return None on CalledProcessError."""
        monkeypatch.setattr(
            subprocess, "run",
            side_effect=subprocess.CalledProcessError(1, "cmd"),
        )
        assert browse.run_command(["cmd"]) is None

    def test_returns_none_on_generic_exception(self, browse, monkeypatch):
        """Should return None on any exception."""
        monkeypatch.setattr(subprocess, "run", side_effect=OSError("fail"))
        assert browse.run_command(["cmd"]) is None

    def test_uses_check_true(self, browse, monkeypatch):
        """Should call subprocess.run with check=True."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        browse.run_command(["cmd"])
        assert calls[0].get("check") is True

    def test_captures_output_and_text(self, browse, monkeypatch):
        """Should capture stdout/stderr and use text mode."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        browse.run_command(["cmd"])
        assert calls[0].get("capture_output") is True
        assert calls[0].get("text") is True


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_exits(self, browse, monkeypatch):
        """Should exit 1 when no URL provided."""
        monkeypatch.setattr(sys, "argv", ["browse"])
        with pytest.raises(SystemExit) as exc_info:
            browse.main()
        assert exc_info.value.code == 1

    def test_too_many_args_exits(self, browse, monkeypatch):
        """Should exit 1 when too many args provided."""
        monkeypatch.setattr(sys, "argv", ["browse", "url1", "url2"])
        with pytest.raises(SystemExit) as exc_info:
            browse.main()
        assert exc_info.value.code == 1

    def test_defuddle_success(self, browse, monkeypatch, capsys):
        """Should print defuddle output and exit 0."""
        def mock_run_command(cmd):
            if cmd[0] == "defuddle":
                return "markdown content"
            return None
        monkeypatch.setitem(browse._ns, "run_command", mock_run_command)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        browse.main()
        out = capsys.readouterr().out
        assert out.strip() == "markdown content"

    def test_curl_html2text_fallback(self, browse, monkeypatch, capsys):
        """Should use curl+html2text when defuddle returns nothing."""
        def mock_run_command(cmd):
            if cmd[0] == "defuddle":
                return None
            if cmd[0] == "curl":
                return "<html><body>Hello</body></html>"
            return None
        monkeypatch.setitem(browse._ns, "run_command", mock_run_command)
        mock_h2t = MagicMock(stdout="Hello\n", returncode=0)
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_h2t)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        browse.main()
        out = capsys.readouterr().out
        assert "Hello" in out

    def test_needs_browser_when_all_fail(self, browse, monkeypatch, capsys):
        """Should print NEEDS_BROWSER and exit 1 when all methods fail."""
        monkeypatch.setitem(browse._ns, "run_command", lambda cmd: None)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        with pytest.raises(SystemExit) as exc_info:
            browse.main()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "NEEDS_BROWSER" in out

    def test_curl_fails_html2text_not_called(self, browse, monkeypatch, capsys):
        """Should skip html2text when curl returns nothing."""
        monkeypatch.setitem(browse._ns, "run_command", lambda cmd: None)
        subproc_calls = []
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: (subproc_calls.append(a), MagicMock())[1])
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        with pytest.raises(SystemExit):
            browse.main()
        assert not any("html2text" in str(c) for c in subproc_calls)

    def test_defuddle_has_priority(self, browse, monkeypatch, capsys):
        """Defuddle output should be used when available (no curl fallback)."""
        call_log = []
        def mock_run_command(cmd):
            call_log.append(cmd[0])
            if cmd[0] == "defuddle":
                return "defuddle content"
            return None
        monkeypatch.setitem(browse._ns, "run_command", mock_run_command)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        browse.main()
        out = capsys.readouterr().out
        assert "defuddle content" in out
        assert "curl" not in call_log

    def test_exits_zero_on_success(self, browse, monkeypatch, capsys):
        """Should not raise SystemExit when content extracted successfully."""
        def mock_run_command(cmd):
            if cmd[0] == "defuddle":
                return "content"
            return None
        monkeypatch.setitem(browse._ns, "run_command", mock_run_command)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        # Should NOT raise SystemExit
        browse.main()

    def test_html2text_empty_falls_through(self, browse, monkeypatch, capsys):
        """Should fall through to NEEDS_BROWSER if html2text returns empty."""
        def mock_run_command(cmd):
            if cmd[0] == "defuddle":
                return None
            if cmd[0] == "curl":
                return "<html></html>"
            return None
        monkeypatch.setitem(browse._ns, "run_command", mock_run_command)
        # html2text returns empty output
        mock_h2t = MagicMock(stdout="  \n", returncode=0)
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_h2t)
        monkeypatch.setattr(sys, "argv", ["browse", "https://example.com"])
        with pytest.raises(SystemExit) as exc_info:
            browse.main()
        assert exc_info.value.code == 1
        assert "NEEDS_BROWSER" in capsys.readouterr().out


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
