#!/usr/bin/env python3
"""Tests for cn-route effector — routing logic and host list management."""

import importlib.util
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Module loading — use importlib for a proper module object so patch.object
# works cleanly on every function.
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "cn_route", "/home/terry/germline/effectors/cn-route"
)
cn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cn)


# ===================================================================
# CN_API_HOSTS
# ===================================================================

class TestCNApiHosts:
    """Validate the static host list covers all providers."""

    def test_not_empty(self):
        assert len(cn.CN_API_HOSTS) > 0

    @pytest.mark.parametrize("keyword", [
        "bigmodel",      # ZhiPu
        "dashscope",     # Alibaba / Bailian
        "minimaxi",      # MiniMax
        "infini-ai",     # Infini (无问芯穹)
        "volces",        # Volcano Engine (火山引擎)
    ])
    def test_major_providers_present(self, keyword):
        assert any(keyword in h for h in cn.CN_API_HOSTS)


# ===================================================================
# _route_cmd
# ===================================================================

class TestRouteCmd:
    def test_root_omits_sudo(self):
        with patch("os.getuid", return_value=0):
            cmd = cn._route_cmd("-n", "add", "1.2.3.4/32", "gw")
            assert cmd == ["/sbin/route", "-n", "add", "1.2.3.4/32", "gw"]

    def test_non_root_prepends_sudo(self):
        with patch("os.getuid", return_value=1000):
            cmd = cn._route_cmd("-n", "add", "1.2.3.4/32", "gw")
            assert cmd == ["sudo", "/sbin/route", "-n", "add", "1.2.3.4/32", "gw"]


# ===================================================================
# _resolve
# ===================================================================

class TestResolve:
    @staticmethod
    def _dig(stdout: str) -> MagicMock:
        return MagicMock(stdout=stdout, returncode=0)

    def test_filters_cnames(self):
        with patch("subprocess.run", return_value=self._dig(
            "cdn.example.com.\n1.2.3.4\n5.6.7.8\nalias.com.\n"
        )):
            assert cn._resolve("host") == ["1.2.3.4", "5.6.7.8"]

    def test_empty_output(self):
        with patch("subprocess.run", return_value=self._dig("")):
            assert cn._resolve("host") == []

    def test_only_cnames(self):
        with patch("subprocess.run", return_value=self._dig(
            "cdn.a.com.\nalias.b.com.\n"
        )):
            assert cn._resolve("host") == []

    def test_strips_whitespace(self):
        with patch("subprocess.run", return_value=self._dig(
            "  1.2.3.4  \n  5.6.7.8  \n"
        )):
            assert cn._resolve("host") == ["1.2.3.4", "5.6.7.8"]

    def test_skips_blank_lines(self):
        with patch("subprocess.run", return_value=self._dig("\n\n1.2.3.4\n\n")):
            assert cn._resolve("host") == ["1.2.3.4"]


# ===================================================================
# _lan_gateway
# ===================================================================

class TestLanGateway:
    def test_finds_en_gateway(self):
        out = "default  192.168.1.1  UGSc  en0\ndefault  10.0.0.1  UGSc  utun0\n"
        with patch("subprocess.run", return_value=MagicMock(stdout=out)):
            assert cn._lan_gateway() == "192.168.1.1"

    def test_no_en_interface_returns_none(self):
        out = "default  10.0.0.1  UGSc  utun0\n"
        with patch("subprocess.run", return_value=MagicMock(stdout=out)):
            assert cn._lan_gateway() is None

    def test_empty_routing_table(self):
        with patch("subprocess.run", return_value=MagicMock(stdout="")):
            assert cn._lan_gateway() is None


# ===================================================================
# _tailscale_exit_active
# ===================================================================

class TestTailscaleExitActive:
    def test_exit_node_active(self):
        data = json.dumps({"Peer": {"n1": {"ExitNode": True}}})
        with patch("subprocess.run", return_value=MagicMock(stdout=data)):
            assert cn._tailscale_exit_active() is True

    def test_no_exit_node(self):
        data = json.dumps({"Peer": {"n1": {"ExitNode": False}}})
        with patch("subprocess.run", return_value=MagicMock(stdout=data)):
            assert cn._tailscale_exit_active() is False

    def test_empty_peers(self):
        with patch("subprocess.run", return_value=MagicMock(stdout='{"Peer": {}}')):
            assert cn._tailscale_exit_active() is False

    def test_exception_returns_false(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert cn._tailscale_exit_active() is False

    def test_bad_json_returns_false(self):
        with patch("subprocess.run", return_value=MagicMock(stdout="not json")):
            assert cn._tailscale_exit_active() is False


# ===================================================================
# _current_zhipu_routes
# ===================================================================

class TestCurrentZhipuRoutes:
    def test_matching_routes(self):
        netstat = "1.2.3.4/32  192.168.1.1  UHSc  en0\n10.0.0.1  10.0.0.1  UH  lo0\n"
        with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
            with patch("subprocess.run", return_value=MagicMock(stdout=netstat)):
                routes = cn._current_zhipu_routes()
        assert routes == {"1.2.3.4/32": "en0"}

    def test_no_matching_routes(self):
        netstat = "10.0.0.1  10.0.0.1  UH  lo0\n"
        with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
            with patch("subprocess.run", return_value=MagicMock(stdout=netstat)):
                assert cn._current_zhipu_routes() == {}


# ===================================================================
# add_routes
# ===================================================================

class TestAddRoutes:
    def test_no_gateway_exits(self):
        with patch.object(cn, "_lan_gateway", return_value=None):
            with pytest.raises(SystemExit) as exc:
                cn.add_routes()
            assert exc.value.code == 1

    def test_no_ips_exits(self):
        with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
            with patch.object(cn, "_resolve", return_value=[]):
                with pytest.raises(SystemExit) as exc:
                    cn.add_routes()
                assert exc.value.code == 1

    def test_success_prints_added(self, capsys):
        with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
            with patch.object(cn, "_resolve", return_value=["1.2.3.4", "5.6.7.8"]):
                with patch.object(cn, "_route_cmd", return_value=["route"]):
                    with patch("subprocess.run", return_value=MagicMock(returncode=0)):
                        cn.add_routes()
        out = capsys.readouterr().out
        assert "2 route(s) added" in out
        assert "1.2.3.4 via 192.168.1.1" in out

    def test_already_in_table(self, capsys):
        fail = MagicMock(returncode=1, stderr="route already in table")
        with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
            with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
                with patch.object(cn, "_route_cmd", return_value=["route"]):
                    with patch("subprocess.run", return_value=fail):
                        cn.add_routes()
        assert "already routed" in capsys.readouterr().out

    def test_failed_route(self, capsys):
        fail = MagicMock(returncode=1, stderr="network unreachable")
        with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
            with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
                with patch.object(cn, "_route_cmd", return_value=["route"]):
                    with patch("subprocess.run", return_value=fail):
                        cn.add_routes()
        assert "failed" in capsys.readouterr().out


# ===================================================================
# remove_routes
# ===================================================================

class TestRemoveRoutes:
    def test_removes_resolved_ips(self, capsys):
        with patch.object(cn, "_resolve", return_value=["1.2.3.4", "5.6.7.8"]):
            with patch.object(cn, "_route_cmd", return_value=["route"]):
                with patch("subprocess.run", return_value=MagicMock()):
                    cn.remove_routes()
        out = capsys.readouterr().out
        assert "- 1.2.3.4" in out
        assert "- 5.6.7.8" in out
        assert "Routes removed" in out

    def test_no_ips_still_completes(self, capsys):
        with patch.object(cn, "_resolve", return_value=[]):
            cn.remove_routes()
        assert "Routes removed" in capsys.readouterr().out


# ===================================================================
# show_status
# ===================================================================

class TestShowStatus:
    def test_no_routes_no_exit(self, capsys):
        with patch.object(cn, "_current_zhipu_routes", return_value={}):
            with patch.object(cn, "_tailscale_exit_active", return_value=False):
                with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
                    with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
                        cn.show_status()
        out = capsys.readouterr().out
        assert "inactive" in out
        assert "No bypass routes needed" in out

    def test_exit_active_no_routes_warns(self, capsys):
        with patch.object(cn, "_current_zhipu_routes", return_value={}):
            with patch.object(cn, "_tailscale_exit_active", return_value=True):
                with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
                    with patch.object(cn, "_resolve", return_value=["1.2.3.4"]):
                        cn.show_status()
        out = capsys.readouterr().out
        assert "active" in out
        assert "No bypass routes set" in out

    def test_direct_route_shows_direct(self, capsys):
        with patch.object(cn, "_current_zhipu_routes",
                          return_value={"1.2.3.4/32": "en0"}):
            with patch.object(cn, "_tailscale_exit_active", return_value=True):
                with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
                    with patch.object(cn, "_resolve", return_value=[]):
                        cn.show_status()
        assert "direct" in capsys.readouterr().out

    def test_utun_route_shows_tunneled(self, capsys):
        with patch.object(cn, "_current_zhipu_routes",
                          return_value={"1.2.3.4/32": "utun3"}):
            with patch.object(cn, "_tailscale_exit_active", return_value=True):
                with patch.object(cn, "_lan_gateway", return_value="192.168.1.1"):
                    with patch.object(cn, "_resolve", return_value=[]):
                        cn.show_status()
        assert "TUNNELED" in capsys.readouterr().out
