"""Tests for effectors/diapedesis — stateful browser automation wrapper."""
from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "diapedesis"
    loader = SourceFileLoader("diapedesis", str(module_path))
    spec = importlib.util.spec_from_loader("diapedesis", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Unit tests: _run helper ──────────────────────────────────────────────


class TestRunHelper:
    def test_success(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok output"
        mock_result.stderr = ""
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        ok, out, err = mod._run(["echo", "test"])
        assert ok is True
        assert out == "ok output"

    def test_failure(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fail"
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        ok, out, err = mod._run(["false"])
        assert ok is False

    def test_timeout(self, monkeypatch):
        mod = _load_module()
        import subprocess as sp
        monkeypatch.setattr(
            mod.subprocess, "run",
            MagicMock(side_effect=sp.TimeoutExpired("cmd", 15)),
        )
        ok, out, err = mod._run(["slow"])
        assert ok is False
        assert err == "timeout"

    def test_not_found(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(
            mod.subprocess, "run",
            MagicMock(side_effect=FileNotFoundError),
        )
        ok, out, err = mod._run(["missing-binary"])
        assert ok is False
        assert "not found" in err


# ── Unit tests: ab wrapper ───────────────────────────────────────────────


class TestAbWrapper:
    def test_ab_success_returns_stdout(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "page html"
        mock_result.stderr = ""
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        ok, out = mod.ab("get", "url")
        assert ok is True
        assert out == "page html"

    def test_ab_failure_returns_stderr(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error msg"
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        ok, out = mod.ab("click", "@e1")
        assert ok is False
        assert "error msg" in out


# ── Unit tests: commands ─────────────────────────────────────────────────


class TestCmdReset:
    def test_reset_calls_kill_and_cleanup(self, monkeypatch, capsys):
        mod = _load_module()
        killed = {"daemons": False, "sockets": False}
        monkeypatch.setattr(mod, "_kill_daemons", lambda: killed.setdefault("daemons", True))
        monkeypatch.setattr(mod, "_cleanup_sockets", lambda: killed.setdefault("sockets", True))
        mod.cmd_reset(MagicMock())
        assert killed["daemons"] is True
        assert killed["sockets"] is True
        assert "Reset complete" in capsys.readouterr().out


class TestCmdOpen:
    def test_open_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "_ensure_session", lambda **kw: None)
        # ab("close") → ok, ab("--profile", ..., "open", url) → ok
        call_num = {"n": 0}

        def fake_ab(*args, timeout=15):
            call_num["n"] += 1
            if args[0] == "close":
                return True, ""
            return True, ""

        monkeypatch.setattr(mod, "ab", fake_ab)
        monkeypatch.setattr(mod, "time", MagicMock())

        args = MagicMock()
        args.url = "https://example.com"
        args.headed = False
        mod.cmd_open(args)
        out = capsys.readouterr().out
        assert "example.com" in out

    def test_open_failure_exits(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "_ensure_session", lambda **kw: None)

        def fake_ab(*args, timeout=15):
            if args[0] == "close":
                return True, ""
            return False, "connection refused"

        monkeypatch.setattr(mod, "ab", fake_ab)
        monkeypatch.setattr(mod, "time", MagicMock())

        args = MagicMock()
        args.url = "https://bad.example.com"
        args.headed = False
        with pytest.raises(SystemExit, match="1"):
            mod.cmd_open(args)


class TestCmdSnap:
    def test_snap_interactive(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "snapshot content"))
        args = MagicMock()
        args.full = False
        mod.cmd_snap(args)
        assert "snapshot content" in capsys.readouterr().out

    def test_snap_full(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "full tree"))
        args = MagicMock()
        args.full = True
        mod.cmd_snap(args)
        assert "full tree" in capsys.readouterr().out

    def test_snap_error(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "not connected"))
        args = MagicMock()
        args.full = False
        mod.cmd_snap(args)
        assert "Error" in capsys.readouterr().out


class TestCmdClick:
    def test_click_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, ""))
        args = MagicMock()
        args.ref = "@e42"
        mod.cmd_click(args)
        assert "Done" in capsys.readouterr().out

    def test_click_failure(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "element not found"))
        args = MagicMock()
        args.ref = "@e999"
        mod.cmd_click(args)
        assert "Error" in capsys.readouterr().out


class TestCmdFill:
    def test_fill_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, ""))
        args = MagicMock()
        args.ref = "@e10"
        args.text = "hello"
        mod.cmd_fill(args)
        assert "Done" in capsys.readouterr().out


class TestCmdSelectEl:
    def test_select_el_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "selected: Option A"))
        args = MagicMock()
        args.text = "Option A"
        mod.cmd_select_el(args)
        assert "selected: Option A" in capsys.readouterr().out

    def test_select_el_not_found(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "not found: Missing"))
        args = MagicMock()
        args.text = "Missing"
        mod.cmd_select_el(args)
        assert "not found" in capsys.readouterr().out


class TestCmdCartAdd:
    def test_cart_add_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "added"))
        args = MagicMock()
        args.selector = "#add-btn"
        mod.cmd_cart_add(args)
        assert "added" in capsys.readouterr().out

    def test_cart_add_button_not_found(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "button not found: #missing"))
        args = MagicMock()
        args.selector = "#missing"
        mod.cmd_cart_add(args)
        assert "not found" in capsys.readouterr().out


class TestCmdSubmit:
    def test_submit_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "submitted 5 fields"))
        args = MagicMock()
        args.follow = False
        mod.cmd_submit(args)
        assert "submitted 5 fields" in capsys.readouterr().out

    def test_submit_with_follow(self, monkeypatch, capsys):
        mod = _load_module()
        calls = {"n": 0}

        def fake_ab(*a, timeout=15):
            calls["n"] += 1
            if calls["n"] == 1:
                return True, "submitted 3 fields"
            return True, "https://example.com/redirect"

        monkeypatch.setattr(mod, "ab", fake_ab)
        monkeypatch.setattr(mod, "time", MagicMock())
        args = MagicMock()
        args.follow = True
        mod.cmd_submit(args)
        out = capsys.readouterr().out
        assert "submitted 3 fields" in out
        assert "Redirected to" in out

    def test_submit_failure(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "eval error"))
        args = MagicMock()
        args.follow = False
        mod.cmd_submit(args)
        assert "Error" in capsys.readouterr().err


class TestCmdScreenshot:
    def test_screenshot_default_path(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, ""))
        args = MagicMock()
        args.path = ""
        mod.cmd_screenshot(args)
        out = capsys.readouterr().out
        assert "diapedesis-screenshot.png" in out

    def test_screenshot_custom_path(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, ""))
        args = MagicMock()
        args.path = "/tmp/custom.png"
        mod.cmd_screenshot(args)
        assert "/tmp/custom.png" in capsys.readouterr().out

    def test_screenshot_failure(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "browser not open"))
        args = MagicMock()
        args.path = "/tmp/test.png"
        mod.cmd_screenshot(args)
        assert "Error" in capsys.readouterr().out


class TestCmdUrl:
    def test_url_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "https://example.com/page"))
        mod.cmd_url(MagicMock())
        assert "https://example.com/page" in capsys.readouterr().out

    def test_url_failure(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "no session"))
        mod.cmd_url(MagicMock())
        assert "Error" in capsys.readouterr().out


class TestCmdTitle:
    def test_title_success(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "My Page Title"))
        mod.cmd_title(MagicMock())
        assert "My Page Title" in capsys.readouterr().out

    def test_title_failure(self, monkeypatch, capsys):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "no session"))
        mod.cmd_title(MagicMock())
        assert "Error" in capsys.readouterr().out


# ── Integration: _ensure_session ─────────────────────────────────────────


class TestEnsureSession:
    def test_session_already_running(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (True, "http://page.com"))
        # Should not kill or cleanup since session is responsive
        killed = {"called": False}
        monkeypatch.setattr(mod, "_kill_daemons", lambda: killed.setdefault("called", True))
        mod._ensure_session(headed=False)
        assert killed.get("called") is not True

    def test_session_not_responsive_resets(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "ab", lambda *a, timeout=15: (False, "not running"))
        killed = {"called": False}
        cleaned = {"called": False}
        monkeypatch.setattr(mod, "_kill_daemons", lambda: killed.setdefault("called", True))
        monkeypatch.setattr(mod, "_cleanup_sockets", lambda: cleaned.setdefault("called", True))
        monkeypatch.setattr(mod, "time", MagicMock())
        mod._ensure_session(headed=False)
        assert killed["called"] is True
        assert cleaned["called"] is True


# ── Integration: main CLI ────────────────────────────────────────────────


class TestMainCli:
    def test_no_command_exits(self):
        mod = _load_module()
        with pytest.raises(SystemExit):
            mod.main()  # No args → argparse error

    def test_reset_command(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "_kill_daemons", lambda: None)
        monkeypatch.setattr(mod, "_cleanup_sockets", lambda: None)
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog", "reset"]))
        mod.main()  # Should not raise
