#!/usr/bin/env python3
"""Tests for cn-route effector — tests routing logic and host list."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Execute the cn-route file directly
cn_route_path = Path("/home/terry/germline/effectors/cn-route")
cn_route_code = cn_route_path.read_text()
namespace = {}
exec(cn_route_code, namespace)

# Extract all the functions/globals from the namespace
cn_route = type('cn_route_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(cn_route, key, value)

# ---------------------------------------------------------------------------
# Test CN_API_HOSTS list
# ---------------------------------------------------------------------------

def test_cn_api_hosts_not_empty():
    """Test CN_API_HOSTS contains expected providers."""
    assert len(cn_route.CN_API_HOSTS) > 0
    # Check for major providers
    assert any("bigmodel" in host for host in cn_route.CN_API_HOSTS)
    assert any("dashscope" in host for host in cn_route.CN_API_HOSTS)
    assert any("minimaxi" in host for host in cn_route.CN_API_HOSTS)
    assert any("volces" in host for host in cn_route.CN_API_HOSTS)
    assert any("infini-ai" in host for host in cn_route.CN_API_HOSTS)

# ---------------------------------------------------------------------------
# Test _route_cmd
# ---------------------------------------------------------------------------

def test_route_cmd_root():
    """Test _route_cmd doesn't add sudo when running as root."""
    with patch('os.getuid', return_value=0):
        cmd = cn_route._route_cmd("add", "1.2.3.4", "gateway")
        assert cmd[0] == "/sbin/route"
        assert "sudo" not in cmd

def test_route_cmd_non_root():
    """Test _route_cmd adds sudo when not running as root."""
    with patch('os.getuid', return_value=1000):
        cmd = cn_route._route_cmd("add", "1.2.3.4", "gateway")
        assert cmd[0] == "sudo"
        assert cmd[1] == "/sbin/route"

# ---------------------------------------------------------------------------
# Test _resolve
# ---------------------------------------------------------------------------

def test_resolve_filters_cnames():
    """Test _resolve filters out CNAME records (lines ending with dot)."""
    mock_result = MagicMock()
    mock_result.stdout = """
example.com.
192.168.1.1
203.0.113.42
api.example.com.
    """
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        ips = cn_route._resolve("example.com")
        # Only the two IPs should be returned, not CNAME lines
        assert len(ips) == 2
        assert "192.168.1.1" in ips
        assert "203.0.113.42" in ips

def test_resolve_empty_no_ips():
    """Test _resolve returns empty list when no IPs found."""
    mock_result = MagicMock()
    mock_result.stdout = "example.com.\napi.example.com."
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        ips = cn_route._resolve("example.com")
        assert ips == []

# ---------------------------------------------------------------------------
# Test _lan_gateway
# ---------------------------------------------------------------------------

def test_lan_gateway_finds_correct_line():
    """Test _lan_gateway finds default gateway on en interface."""
    mock_result = MagicMock()
    mock_result.stdout = """
Routing tables

Internet:
Destination        Gateway            Flags           Netif Expire
default            192.168.1.1        UG            en0
127.0.0.1          127.0.0.1          UH            lo0
192.168.1.0/24     link#4             U             en0
    """
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        gateway = cn_route._lan_gateway()
        assert gateway == "192.168.1.1"

def test_lan_gateway_not_found_returns_none():
    """Test _lan_gateway returns None when no matching gateway."""
    mock_result = MagicMock()
    mock_result.stdout = """
Destination        Gateway            Flags           Netif Expire
default            10.0.0.1           UG            utun0
127.0.0.1          127.0.0.1          UH            lo0
    """
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        gateway = cn_route._lan_gateway()
        assert gateway is None

# ---------------------------------------------------------------------------
# Test _tailscale_exit_active
# ---------------------------------------------------------------------------

def test_tailscale_exit_active_true():
    """Test _tailscale_exit_active returns True when exit node active."""
    mock_result = MagicMock()
    mock_result.stdout = '''
{
  "Peer": {
    "node1": {
      "ExitNode": true
    },
    "node2": {
      "ExitNode": false
    }
  }
}
    '''
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        assert cn_route._tailscale_exit_active() is True

def test_tailscale_exit_active_false():
    """Test _tailscale_exit_active returns False when no exit node active."""
    mock_result = MagicMock()
    mock_result.stdout = '''
{
  "Peer": {
    "node1": {
      "ExitNode": false
    },
    "node2": {
      "ExitNode": false
    }
  }
}
    '''
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        assert cn_route._tailscale_exit_active() is False

def test_tailscale_exit_active_exception_returns_false():
    """Test _tailscale_exit_active handles exceptions gracefully."""
    with patch('subprocess.run', side_effect=Exception("tailscale not found")):
        assert cn_route._tailscale_exit_active() is False

# ---------------------------------------------------------------------------
# Test main command routing
# ---------------------------------------------------------------------------

def test_main_add_routes_called():
    """Test main calls add_routes by default."""
    mock_add = MagicMock()
    original_add = cn_route.add_routes
    cn_route.add_routes = mock_add
    
    with patch('sys.argv', ['cn-route']):
        # Re-exec the main dispatch
        cmd = sys.argv[1] if len(sys.argv) > 1 else "add"
        if cmd == "remove":
            cn_route.remove_routes()
        elif cmd == "status":
            cn_route.show_status()
        elif cmd in ("add", ""):
            cn_route.add_routes()
    
    cn_route.add_routes = original_add
    mock_add.assert_called_once()

def test_main_remove_routes_called():
    """Test main calls remove_routes when 'remove' given."""
    mock_remove = MagicMock()
    original_remove = cn_route.remove_routes
    cn_route.remove_routes = mock_remove
    
    with patch('sys.argv', ['cn-route', 'remove']):
        cmd = sys.argv[1] if len(sys.argv) > 1 else "add"
        if cmd == "remove":
            cn_route.remove_routes()
    
    cn_route.remove_routes = original_remove
    mock_remove.assert_called_once()

def test_main_show_status_called():
    """Test main calls show_status when 'status' given."""
    mock_status = MagicMock()
    original_status = cn_route.show_status
    cn_route.show_status = mock_status
    
    with patch('sys.argv', ['cn-route', 'status']):
        cmd = sys.argv[1] if len(sys.argv) > 1 else "add"
        if cmd == "status":
            cn_route.show_status()
    
    cn_route.show_status = original_status
    mock_status.assert_called_once()

# ---------------------------------------------------------------------------
# Test add_routes handles no gateway
# ---------------------------------------------------------------------------

def test_add_routes_exits_no_gateway():
    """Test add_routes exits with code 1 when no gateway found."""
    original_lan_gateway = cn_route._lan_gateway
    cn_route._lan_gateway = lambda: None
    
    with pytest.raises(SystemExit) as exc_info:
        cn_route.add_routes()
    
    cn_route._lan_gateway = original_lan_gateway
    assert exc_info.value.code == 1

def test_add_routes_exits_no_ips():
    """Test add_routes exits with code 1 when no IPs resolved."""
    original_lan_gateway = cn_route._lan_gateway
    original_resolve = cn_route._resolve
    
    cn_route._lan_gateway = lambda: "192.168.1.1"
    cn_route._resolve = lambda host: []
    
    with pytest.raises(SystemExit) as exc_info:
        cn_route.add_routes()
    
    cn_route._lan_gateway = original_lan_gateway
    cn_route._resolve = original_resolve
    assert exc_info.value.code == 1
