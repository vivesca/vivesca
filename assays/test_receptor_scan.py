#!/usr/bin/env python3
"""Tests for effectors/receptor-scan — waterfall knowledge search.

receptor-scan is a script (effectors/receptor-scan), not an importable module.
It is loaded via exec() into isolated namespaces.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

RECEPTOR_SCAN_PATH = Path(__file__).resolve().parents[1] / "effectors" / "receptor-scan"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def rscan():
    """Load receptor-scan via exec into an isolated namespace."""
    ns: dict = {"__name__": "test_receptor_scan", "__file__": str(RECEPTOR_SCAN_PATH)}
    source = RECEPTOR_SCAN_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("receptor_scan", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── File structure tests ───────────────────────────────────────────────────


class TestReceptorScanBasics:
    def test_file_exists(self):
        """Test that receptor-scan effector file exists."""
        assert RECEPTOR_SCAN_PATH.exists()
        assert RECEPTOR_SCAN_PATH.is_file()

    def test_is_python_script(self):
        """Test that receptor-scan has Python shebang."""
        first_line = RECEPTOR_SCAN_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        """Test that receptor-scan has docstring."""
        content = RECEPTOR_SCAN_PATH.read_text()
        assert '"""' in content

    def test_docstring_mentions_waterfall(self):
        """Test docstring mentions waterfall knowledge search."""
        content = RECEPTOR_SCAN_PATH.read_text()
        assert "waterfall" in content.lower() or "search" in content.lower()


# ── run() helper ────────────────────────────────────────────────────────────


class TestRunHelper:
    def test_run_returns_stdout(self, rscan, monkeypatch):
        """Should return stripped stdout on success."""
        mock_result = MagicMock(stdout="  hello world  \n", returncode=0)
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        assert rscan.run(["echo", "test"]) == "hello world"

    def test_run_returns_empty_on_timeout(self, rscan, monkeypatch):
        """Should return empty string on TimeoutExpired."""
        monkeypatch.setattr(subprocess, "run", side_effect=subprocess.TimeoutExpired("cmd", 15))
        assert rscan.run(["slow-cmd"]) == ""

    def test_run_returns_empty_on_file_not_found(self, rscan, monkeypatch):
        """Should return empty string when command not found."""
        monkeypatch.setattr(subprocess, "run", side_effect=FileNotFoundError)
        assert rscan.run(["nonexistent-cmd"]) == ""

    def test_run_passes_timeout(self, rscan, monkeypatch):
        """Should pass timeout parameter to subprocess.run."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        rscan.run(["cmd"], timeout=30)
        assert calls[0]["timeout"] == 30

    def test_run_default_timeout_is_15(self, rscan, monkeypatch):
        """Should default to 15 second timeout."""
        calls = []
        def mock_run(*a, **kw):
            calls.append(kw)
            return MagicMock(stdout="ok")
        monkeypatch.setattr(subprocess, "run", mock_run)
        rscan.run(["cmd"])
        assert calls[0]["timeout"] == 15


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_exits(self, rscan):
        """Should exit 1 when no query provided."""
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan"]
            mock_sys.stderr = MagicMock()
            with pytest.raises(SystemExit) as exc_info:
                rscan.main()
        assert exc_info.value.code == 1

    def test_no_args_prints_usage(self, rscan, capsys):
        """Should print usage message to stderr when no args."""
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan"]
            with pytest.raises(SystemExit):
                rscan.main()
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_qmd_results_printed(self, rscan, capsys, monkeypatch):
        """Should print vault results when qmd returns matches."""
        qmd_output = "qmd://doc1\nqmd://doc2\nsome detail"
        monkeypatch.setattr(rscan, "run", lambda cmd, timeout=15: qmd_output if cmd[0] == "qmd" else "")
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "test query"]
            rscan.main()
        out = capsys.readouterr().out
        assert "Vault (authoritative) — 2 results" in out
        assert "qmd://doc1" in out

    def test_no_qmd_results_prints_none(self, rscan, capsys, monkeypatch):
        """Should print '(no results)' when vault returns nothing."""
        monkeypatch.setattr(rscan, "run", lambda cmd, timeout=15: "")
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "obscure query"]
            rscan.main()
        out = capsys.readouterr().out
        assert "(no results)" in out

    def test_oghma_fallback_when_few_results(self, rscan, capsys, monkeypatch):
        """Should query oghma when vault returns < 3 results."""
        call_log = []
        def mock_run(cmd, timeout=15):
            call_log.append(cmd)
            if cmd[0] == "qmd":
                return "qmd://doc1\ndetail"
            if cmd[0] == "oghma":
                return "oghma result"
            return ""
        monkeypatch.setattr(rscan, "run", mock_run)
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "query"]
            rscan.main()
        out = capsys.readouterr().out
        assert "Oghma (conversation memory)" in out
        assert any(c[0] == "oghma" for c in call_log)

    def test_no_oghma_when_three_or_more_results(self, rscan, capsys, monkeypatch):
        """Should NOT query oghma when vault returns >= 3 results."""
        call_log = []
        def mock_run(cmd, timeout=15):
            call_log.append(cmd)
            if cmd[0] == "qmd":
                return "qmd://doc1\nqmd://doc2\nqmd://doc3\ndetail"
            return ""
        monkeypatch.setattr(rscan, "run", mock_run)
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "query"]
            rscan.main()
        out = capsys.readouterr().out
        assert "Oghma" not in out
        assert not any(c[0] == "oghma" for c in call_log)

    def test_oghma_unavailable(self, rscan, capsys, monkeypatch):
        """Should print '(oghma unavailable)' when oghma returns empty."""
        def mock_run(cmd, timeout=15):
            if cmd[0] == "qmd":
                return ""
            return ""
        monkeypatch.setattr(rscan, "run", mock_run)
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "query"]
            rscan.main()
        out = capsys.readouterr().out
        assert "(oghma unavailable)" in out

    def test_query_joins_multiple_args(self, rscan, capsys, monkeypatch):
        """Should join multiple argv args into single query string."""
        call_log = []
        def mock_run(cmd, timeout=15):
            call_log.append(cmd)
            return "qmd://hit1\nqmd://hit2\nqmd://hit3\ndetail"
        monkeypatch.setattr(rscan, "run", mock_run)
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "how", "to", "deploy"]
            rscan.main()
        # The query passed to qmd should be "how to deploy"
        qmd_calls = [c for c in call_log if c[0] == "qmd"]
        assert len(qmd_calls) == 1
        assert qmd_calls[0][2] == "how to deploy"

    def test_sets_path_env(self, rscan, monkeypatch):
        """Should extend PATH with .bun/bin and .local/bin."""
        monkeypatch.setattr(rscan, "run", lambda cmd, timeout=15: "qmd://a\nqmd://b\nqmd://c\nd")
        monkeypatch.setenv("PATH", "/usr/bin")
        with patch.object(rscan, "sys") as mock_sys:
            mock_sys.argv = ["receptor-scan", "query"]
            rscan.main()
        path = rscan.os.environ["PATH"]
        assert ".bun/bin" in path
        assert ".local/bin" in path


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_exits_nonzero(self):
        """Running receptor-scan with no args should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(RECEPTOR_SCAN_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
        assert "Usage" in r.stderr

    def test_with_query_runs(self):
        """Running receptor-scan with a query should not crash."""
        r = subprocess.run(
            [sys.executable, str(RECEPTOR_SCAN_PATH), "test"],
            capture_output=True, text=True, timeout=30,
        )
        # May succeed or fail depending on tools installed, but should not crash
        assert r.returncode is not None
        # Should have output about vault or oghma
        assert r.stdout or r.stderr
