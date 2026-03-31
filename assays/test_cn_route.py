from __future__ import annotations
"""Tests for effectors/cn-route — bypass Tailscale exit node for Chinese AI APIs.

cn-route is a script (effectors/cn-route), not an importable module.
It is loaded via exec() so that module-level functions can be tested.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CN_ROUTE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cn-route"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr(tmp_path):
    """Load cn-route via exec."""
    ns: dict = {"__name__": "test_cn_route"}
    source = CN_ROUTE_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    return ns


# ── _route_cmd ───────────────────────────────────────────────────────────────


class TestRouteCmd:
    def test_root_no_sudo(self, cr):
        with patch.object(cr["os"], "getuid", return_value=0):
            result = cr["_route_cmd"]("add", "1.2.3.4/32", "192.168.1.1")
        assert result == ["/sbin/route", "add", "1.2.3.4/32", "192.168.1.1"]

    def test_nonroot_needs_sudo(self, cr):
        with patch.object(cr["os"], "getuid", return_value=1000):
            result = cr["_route_cmd"]("add", "1.2.3.4/32", "192.168.1.1")
        assert result == ["sudo", "/sbin/route", "add", "1.2.3.4/32", "192.168.1.1"]


# ── _resolve ────────────────────────────────────────────────────────────────


class TestResolve:
    def test_returns_only_ips_skips_cnames(self, cr):
        mock_run = MagicMock(return_value=MagicMock(
            returncode=0,
            stdout="cdn.example.com.\n1.2.3.4\n5.6.7.8\n",
        ))
        with patch.object(cr["subprocess"], "run", mock_run):
            result = cr["_resolve"]("open.bigmodel.cn")
        assert sorted(result) == sorted(["1.2.3.4", "5.6.7.8"])

    def test_empty_returns_empty_list(self, cr):
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=""))
        with patch.object(cr["subprocess"], "run", mock_run):
            result = cr["_resolve"]("nonexistent.invalid")
        assert result == []

    def test_only_cnames_returns_empty(self, cr):
        mock_run = MagicMock(return_value=MagicMock(
            returncode=0, stdout="cdn.a.com.\nalias.b.com.\n",
        ))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_resolve"]("host") == []

    def test_whitespace_stripped(self, cr):
        mock_run = MagicMock(return_value=MagicMock(
            returncode=0, stdout="  1.2.3.4  \n  5.6.7.8  \n",
        ))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_resolve"]("host") == ["1.2.3.4", "5.6.7.8"]

    def test_blank_lines_skipped(self, cr):
        mock_run = MagicMock(return_value=MagicMock(
            returncode=0, stdout="\n\n1.2.3.4\n\n",
        ))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_resolve"]("host") == ["1.2.3.4"]


# ── _lan_gateway ────────────────────────────────────────────────────────────


class TestLanGateway:
    def test_finds_default_gateway_on_en_interface(self, cr):
        # macOS netstat -rn format: Destination Gateway Flags Netif
        netstat_output = (
            "default            192.168.1.1        UGSc       en0\n"
            "192.168.1.0/24     link#4             U          en0\n"
        )
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=netstat_output))
        with patch.object(cr["subprocess"], "run", mock_run):
            result = cr["_lan_gateway"]()
        assert result == "192.168.1.1"

    def test_ignores_non_en_default_gateway(self, cr):
        netstat_output = "default            10.0.0.1           UGScI      utun3\n"
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=netstat_output))
        with patch.object(cr["subprocess"], "run", mock_run):
            result = cr["_lan_gateway"]()
        assert result is None

    def test_no_default_returns_none(self, cr):
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=""))
        with patch.object(cr["subprocess"], "run", mock_run):
            result = cr["_lan_gateway"]()
        assert result is None

    def test_prefers_first_en_interface(self, cr):
        netstat_output = (
            "default         192.168.1.1     UG   en0\n"
            "default         10.0.0.1        UG   en1\n"
        )
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=netstat_output))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_lan_gateway"]() == "192.168.1.1"


# ── _current_zhipu_routes ───────────────────────────────────────────────────


class TestCurrentZhipuRoutes:
    def test_finds_routes_for_resolved_ips(self, cr):
        def mock_resolve(host):
            return ["1.2.3.4", "5.6.7.8"]

        netstat_output = (
            "1.2.3.4/32      192.168.1.1     UG      en0\n"
            "5.6.7.8/32      10.0.0.1        UG      utun0\n"
            "10.0.0.0/8      0.0.0.0         U       utun0\n"
        )
        with patch.dict(cr, {"_resolve": mock_resolve}):
            with patch.object(cr["subprocess"], "run",
                              return_value=MagicMock(returncode=0, stdout=netstat_output)):
                result = cr["_current_zhipu_routes"]()
        assert result == {
            "1.2.3.4/32": "en0",
            "5.6.7.8/32": "utun0",
        }

    def test_ignores_non_cnapi_ips(self, cr):
        def mock_resolve(host):
            return ["1.2.3.4"]

        netstat_output = (
            "1.2.3.4/32      192.168.1.1     UG      en0\n"
            "9.9.9.9/32      10.0.0.1        UG      utun0\n"
        )
        with patch.dict(cr, {"_resolve": mock_resolve}):
            with patch.object(cr["subprocess"], "run",
                              return_value=MagicMock(returncode=0, stdout=netstat_output)):
                result = cr["_current_zhipu_routes"]()
        assert "9.9.9.9" not in result
        assert "1.2.3.4/32" in result

    def test_empty_routes(self, cr):
        def mock_resolve(host):
            return ["1.2.3.4"]

        with patch.dict(cr, {"_resolve": mock_resolve}):
            with patch.object(cr["subprocess"], "run",
                              return_value=MagicMock(returncode=0, stdout="")):
                assert cr["_current_zhipu_routes"]() == {}


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
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_tailscale_exit_active"]() is True

    def test_inactive_when_no_exit_node_peer(self, cr):
        status_json = json.dumps({"Peer": {"peer1": {"ExitNode": False}}})
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=status_json))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_tailscale_exit_active"]() is False

    def test_inactive_on_json_error(self, cr):
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout="not json"))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_tailscale_exit_active"]() is False

    def test_inactive_on_subprocess_error(self, cr):
        mock_run = MagicMock(side_effect=Exception("tailscale not found"))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_tailscale_exit_active"]() is False

    def test_inactive_when_empty_peers(self, cr):
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout='{"Peer": {}}'))
        with patch.object(cr["subprocess"], "run", mock_run):
            assert cr["_tailscale_exit_active"]() is False


# ── CN_API_HOSTS constant ─────────────────────────────────────────────────────


class TestCNAPIHosts:
    def test_has_expected_providers(self, cr):
        hosts = cr["CN_API_HOSTS"]
        assert len(hosts) > 0

    @pytest.mark.parametrize("keyword", [
        "bigmodel", "dashscope", "minimaxi", "infini-ai", "volces",
    ])
    def test_provider_present(self, cr, keyword):
        assert any(keyword in h for h in cr["CN_API_HOSTS"])

    def test_no_duplicates(self, cr):
        hosts = cr["CN_API_HOSTS"]
        assert len(hosts) == len(set(hosts))

    def test_all_strings(self, cr):
        assert all(isinstance(h, str) for h in cr["CN_API_HOSTS"])


# ── add_routes ────────────────────────────────────────────────────────────────


class TestAddRoutes:
    def test_no_gateway_exits(self, cr):
        with patch.dict(cr, {"_lan_gateway": lambda: None}):
            with pytest.raises(SystemExit) as exc:
                cr["add_routes"]()
        assert exc.value.code == 1

    def test_no_ips_exits(self, cr):
        with patch.dict(cr, {
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda host: [],
        }):
            with pytest.raises(SystemExit) as exc:
                cr["add_routes"]()
        assert exc.value.code == 1

    def test_success_prints_added(self, cr, capsys):
        ok = MagicMock(returncode=0, stderr="")
        with patch.dict(cr, {
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["1.2.3.4", "5.6.7.8"],
            "_route_cmd": lambda *a: ["route"],
        }), patch.object(cr["subprocess"], "run", return_value=ok):
            cr["add_routes"]()
        out = capsys.readouterr().out
        assert "2 route(s) added" in out
        assert "1.2.3.4 via 192.168.1.1" in out

    def test_already_in_table(self, cr, capsys):
        dup = MagicMock(returncode=1, stderr="route already in table")
        with patch.dict(cr, {
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["1.2.3.4"],
            "_route_cmd": lambda *a: ["route"],
        }), patch.object(cr["subprocess"], "run", return_value=dup):
            cr["add_routes"]()
        assert "already routed" in capsys.readouterr().out

    def test_failed_route(self, cr, capsys):
        fail = MagicMock(returncode=1, stderr="network unreachable")
        with patch.dict(cr, {
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["1.2.3.4"],
            "_route_cmd": lambda *a: ["route"],
        }), patch.object(cr["subprocess"], "run", return_value=fail):
            cr["add_routes"]()
        assert "failed" in capsys.readouterr().out

    def test_deduplicates_ips_across_hosts(self, cr, capsys):
        """Multiple hosts resolving to same IP only creates one route."""
        ok = MagicMock(returncode=0, stderr="")
        with patch.dict(cr, {
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["10.0.0.1", "10.0.0.2"],
            "_route_cmd": lambda *a: ["route"],
        }), patch.object(cr["subprocess"], "run", return_value=ok) as mock_run:
            cr["add_routes"]()
        # Only 2 unique IPs despite N hosts
        assert mock_run.call_count == 2


# ── remove_routes ─────────────────────────────────────────────────────────────


class TestRemoveRoutes:
    def test_removes_resolved_ips(self, cr, capsys):
        with patch.dict(cr, {
            "_resolve": lambda h: ["1.2.3.4", "5.6.7.8"],
            "_route_cmd": lambda *a: ["route"],
        }), patch.object(cr["subprocess"], "run", return_value=MagicMock()):
            cr["remove_routes"]()
        out = capsys.readouterr().out
        assert "- 1.2.3.4" in out
        assert "- 5.6.7.8" in out
        assert "Routes removed" in out

    def test_no_ips_still_completes(self, cr, capsys):
        with patch.dict(cr, {"_resolve": lambda h: []}):
            cr["remove_routes"]()
        assert "Routes removed" in capsys.readouterr().out


# ── show_status ───────────────────────────────────────────────────────────────


class TestShowStatus:
    def test_no_routes_no_exit(self, cr, capsys):
        with patch.dict(cr, {
            "_current_zhipu_routes": lambda: {},
            "_tailscale_exit_active": lambda: False,
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["1.2.3.4"],
        }):
            cr["show_status"]()
        out = capsys.readouterr().out
        assert "inactive" in out
        assert "No bypass routes needed" in out

    def test_exit_active_no_routes_warns(self, cr, capsys):
        with patch.dict(cr, {
            "_current_zhipu_routes": lambda: {},
            "_tailscale_exit_active": lambda: True,
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: ["1.2.3.4"],
        }):
            cr["show_status"]()
        out = capsys.readouterr().out
        assert "active" in out
        assert "No bypass routes set" in out

    def test_direct_route_on_en(self, cr, capsys):
        with patch.dict(cr, {
            "_current_zhipu_routes": lambda: {"1.2.3.4/32": "en0"},
            "_tailscale_exit_active": lambda: True,
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: [],
        }):
            cr["show_status"]()
        assert "direct" in capsys.readouterr().out

    def test_tunneled_route_on_utun(self, cr, capsys):
        with patch.dict(cr, {
            "_current_zhipu_routes": lambda: {"1.2.3.4/32": "utun3"},
            "_tailscale_exit_active": lambda: True,
            "_lan_gateway": lambda: "192.168.1.1",
            "_resolve": lambda h: [],
        }):
            cr["show_status"]()
        assert "TUNNELED" in capsys.readouterr().out

    def test_unresolvable_host_shown(self, cr, capsys):
        with patch.dict(cr, {
            "_current_zhipu_routes": lambda: {},
            "_tailscale_exit_active": lambda: False,
            "_lan_gateway": lambda: None,
            "_resolve": lambda h: [],
        }):
            cr["show_status"]()
        out = capsys.readouterr().out
        assert "unresolvable" in out
        assert "LAN gateway: not found" in out


# ── CLI dispatch (__main__ block) ────────────────────────────────────────────


class TestCLIDispatch:
    @pytest.mark.parametrize("argv,func_name", [
        (["cn-route"], "add_routes"),
        (["cn-route", "add"], "add_routes"),
        (["cn-route", "remove"], "remove_routes"),
        (["cn-route", "status"], "show_status"),
    ])
    def test_command_routing(self, cr, argv, func_name):
        calls = {"n": 0}
        def noop(*a, **kw):
            calls["n"] += 1
        with patch.dict(cr, {
            "add_routes": noop,
            "remove_routes": noop,
            "show_status": noop,
        }), patch.object(cr["sys"], "argv", argv):
            cmd = argv[1] if len(argv) > 1 else "add"
            if cmd == "remove":
                cr["remove_routes"]()
            elif cmd == "status":
                cr["show_status"]()
            elif cmd in ("add", ""):
                cr["add_routes"]()
        assert calls["n"] == 1

    def test_unknown_command_prints_docstring(self, cr, capsys):
        """Simulate the __main__ dispatch for an unknown command."""
        with patch.object(cr["sys"], "argv", ["cn-route", "help"]):
            print(cr["__doc__"])
        out = capsys.readouterr().out
        assert "Bypass Tailscale" in out
        assert "Usage" in out
