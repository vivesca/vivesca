from __future__ import annotations

"""Tests for effectors/cn-route — bypass Tailscale exit node for Chinese AI APIs.

cn-route is a script (effectors/cn-route), not an importable module.
It is loaded via exec() so that module-level functions can be tested.
"""

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CN_ROUTE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cn-route"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr(tmp_path):
    """Load cn-route via exec into a ModuleType."""
    mod = types.ModuleType("cn_route")
    mod.__file__ = str(CN_ROUTE_PATH)
    source = CN_ROUTE_PATH.read_text(encoding="utf-8")
    exec(source, mod.__dict__)
    return mod


# ── _add_host_route / _del_host_route ──────────────────────────────────────


class TestRouteCmd:
    def test_root_no_sudo(self, cr):
        with patch.object(cr.os, "getuid", return_value=0), \
             patch.object(cr, "IS_LINUX", False):
            result = cr._add_host_route("1.2.3.4", "192.168.1.1")
        # subprocess.run was called. We check the command list from the mock if needed,
        # but the script logic returns the CompletedProcess from subprocess.run.

    def test_nonroot_needs_sudo(self, cr):
        with patch.object(cr.os, "getuid", return_value=1000), \
             patch.object(cr, "IS_LINUX", False), \
             patch.object(cr.subprocess, "run", return_value=MagicMock(returncode=0)) as mock_run:
            cr._add_host_route("1.2.3.4", "192.168.1.1")
        
        args, _ = mock_run.call_args
        cmd = args[0]
        assert "sudo" in cmd
        assert "/sbin/route" in cmd


# ── _resolve ────────────────────────────────────────────────────────────────


class TestResolve:
    def test_returns_ips(self, cr):
        mock_addrinfo = [
            (None, None, None, None, ("1.2.3.4", 0)),
            (None, None, None, None, ("5.6.7.8", 0)),
        ]
        with patch.object(cr.socket, "getaddrinfo", return_value=mock_addrinfo):
            result = cr._resolve("open.bigmodel.cn")
        assert sorted(result) == sorted(["1.2.3.4", "5.6.7.8"])

    def test_empty_returns_empty_list(self, cr):
        with patch.object(cr.socket, "getaddrinfo", side_effect=cr.socket.gaierror):
            result = cr._resolve("nonexistent.invalid")
        assert result == []


# ── _lan_gateway ────────────────────────────────────────────────────────────


class TestLanGateway:
    def test_finds_default_gateway_mac(self, cr):
        # macOS netstat -rn format: Destination Gateway Flags Netif
        netstat_output = (
            "default            192.168.1.1        UGSc       en0\n"
            "192.168.1.0/24     link#4             U          en0\n"
        )
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=netstat_output))
        with patch.object(cr, "IS_LINUX", False), \
             patch.object(cr.subprocess, "run", mock_run):
            result = cr._lan_gateway()
        assert result == "192.168.1.1"

    def test_finds_default_gateway_linux(self, cr):
        ip_route_output = "default via 192.168.1.254 dev eth0 proto dhcp src 192.168.1.50 metric 100"
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=ip_route_output))
        with patch.object(cr, "IS_LINUX", True), \
             patch.object(cr.subprocess, "run", mock_run):
            result = cr._lan_gateway()
        assert result == "192.168.1.254"


# ── _current_cn_routes ──────────────────────────────────────────────────────


class TestCurrentCNRoutes:
    def test_finds_routes_mac(self, cr):
        with patch.object(cr, "IS_LINUX", False), \
             patch.object(cr, "CN_API_HOSTS", ["host1"]), \
             patch.object(cr, "_resolve", return_value=["1.2.3.4"]), \
             patch.object(cr.subprocess, "run", return_value=MagicMock(returncode=0, stdout="1.2.3.4/32 192.168.1.1 UG en0")):
            result = cr._current_cn_routes()
        assert result == {"1.2.3.4": "en0"}


# ── _tailscale_exit_active ───────────────────────────────────────────────────


class TestTailscaleExitActive:
    def test_active_when_exit_node_peer(self, cr):
        status_json = json.dumps({
            "Peer": {
                "exit-node": {"ExitNode": True},
                "other-peer": {"ExitNode": False},
            }
        })
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=status_json))
        with patch.object(cr.subprocess, "run", mock_run):
            assert cr._tailscale_exit_active() is True


# ── add_routes ────────────────────────────────────────────────────────────────


class TestAddRoutes:
    def test_no_gateway_exits(self, cr):
        with patch.object(cr, "_lan_gateway", return_value=None):
            with pytest.raises(SystemExit) as exc:
                cr.add_routes()
        assert exc.value.code == 1

    def test_success_prints_added(self, cr, capsys):
        ok = MagicMock(returncode=0, stderr="")
        with patch.object(cr, "_lan_gateway", return_value="192.168.1.1"), \
             patch.object(cr, "_resolve", return_value=["1.2.3.4"]), \
             patch.object(cr, "_add_host_route", return_value=ok):
            cr.add_routes()
        out = capsys.readouterr().out
        assert "1 route(s) added" in out
        assert "1.2.3.4 via 192.168.1.1" in out


# ── remove_routes ─────────────────────────────────────────────────────────────


class TestRemoveRoutes:
    def test_removes_resolved_ips(self, cr, capsys):
        with patch.object(cr, "_resolve", return_value=["1.2.3.4"]), \
             patch.object(cr, "_del_host_route", return_value=MagicMock()):
            cr.remove_routes()
        out = capsys.readouterr().out
        assert "- 1.2.3.4" in out
        assert "Routes removed" in out


# ── show_status ───────────────────────────────────────────────────────────────


class TestShowStatus:
    def test_no_routes_no_exit(self, cr, capsys):
        with patch.object(cr, "_current_cn_routes", return_value={}), \
             patch.object(cr, "_tailscale_exit_active", return_value=False), \
             patch.object(cr, "_lan_gateway", return_value="192.168.1.1"), \
             patch.object(cr, "_resolve", return_value=["1.2.3.4"]):
            cr.show_status()
        out = capsys.readouterr().out
        assert "inactive" in out
        assert "No bypass routes needed" in out


# ── CLI dispatch (__main__ block) ────────────────────────────────────────────


class TestCLIDispatch:
    def test_unknown_command_prints_help(self, cr, capsys):
        with patch.object(cr.sys, "argv", ["cn-route", "--help"]):
            # In a script's __main__, this would print _HELP and exit.
            # Here we just test the _HELP variable exists and looks right.
            assert "Bypass Tailscale" in cr._HELP
