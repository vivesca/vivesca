#!/usr/bin/env python3
"""Test for oci-arm-retry effector. Mocks subprocess to avoid actual instance launches."""
import json
import subprocess
import sys
from pathlib import Path
import pytest


def test_script_runs_with_help():
    """Test that the script runs and shows help without errors."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    assert effector_path.exists(), f"Effector not found at {effector_path}"
    
    result = subprocess.run(
        [sys.executable, str(effector_path), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "Retry OCI ARM A1 instance launch" in result.stdout
    assert "--loop" in result.stdout
    assert "--max-attempts" in result.stdout


def test_parse_args(monkeypatch):
    """Test argument parsing by executing the script with mocked subprocess."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    
    # Capture argparse output by mocking sys.argv and exiting before main logic
    ns = {}
    with open(effector_path) as f:
        source = f.read()
    
    # Patch sys.argv for testing
    monkeypatch.setattr(sys, "argv", ["oci-arm-retry", "--loop", "--multi", "--interval", "600", "--max-attempts", "10"])
    
    # Mock subprocess.run early to prevent actual OCI calls
    called = []
    def mock_run(cmd, *args, **kwargs):
        called.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="{}")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    # Execute the script up to main
    exec(source, ns)
    # We should be able to call main without errors (it will exit after first attempt)
    with pytest.raises(SystemExit) as excinfo:
        ns["main"]()
    # Should exit with 1 because the mock launch failed
    assert excinfo.value.code == 1


def test_try_launch_success(monkeypatch):
    """Test try_launch returns data on success."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    ns = {}
    with open(effector_path) as f:
        source = f.read()
    
    called_cmd = None
    def mock_run(cmd, *args, **kwargs):
        nonlocal called_cmd
        called_cmd = cmd
        success_output = json.dumps({
            "data": {
                "id": "ocid1.instance.oc1.ap-tokyo-1.aaaaaaaaaaaaaaa",
                "lifecycle-state": "RUNNING"
            }
        })
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=success_output, stderr="")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    exec(source, ns)
    config = ns["DEFAULT_CONFIG"]
    result = ns["try_launch"](config)
    
    assert called_cmd is not None, "subprocess.run was not called"
    assert "oci" in called_cmd
    assert "launch" in called_cmd
    assert result is not None
    assert result["id"] == "ocid1.instance.oc1.ap-tokyo-1.aaaaaaaaaaaaaaa"
    assert result["lifecycle-state"] == "RUNNING"


def test_try_launch_out_of_capacity(monkeypatch):
    """Test try_launch returns None when out of capacity."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    ns = {}
    with open(effector_path) as f:
        source = f.read()
    
    called = []
    def mock_run(cmd, *args, **kwargs):
        called.append(cmd)
        error_output = json.dumps({
            "code": "OutofCapacity",
            "message": "Out of capacity for shape VM.Standard.A1.Flex in availability domain"
        })
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=error_output)
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    exec(source, ns)
    config = ns["DEFAULT_CONFIG"]
    result = ns["try_launch"](config)
    
    assert result is None


def test_get_subscribed_regions_success(monkeypatch):
    """Test get_subscribed_regions returns correct regions."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    ns = {}
    with open(effector_path) as f:
        source = f.read()
    
    mock_output = json.dumps({
        "data": [
            {"region-name": "ap-tokyo-1"},
            {"region-name": "ap-osaka-1"},
            {"region-name": "ap-sydney-1"}
        ]
    })
    
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], returncode=0, stdout=mock_output, stderr="")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    exec(source, ns)
    regions = ns["get_subscribed_regions"]()
    
    assert sorted(regions) == sorted(["ap-tokyo-1", "ap-osaka-1", "ap-sydney-1"])


def test_get_subscribed_regions_fallback(monkeypatch):
    """Test get_subscribed_regions falls back to default ap-tokyo-1 on error."""
    effector_path = Path(__file__).parent.parent / "effectors" / "oci-arm-retry"
    ns = {}
    with open(effector_path) as f:
        source = f.read()
    
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], returncode=1, stdout="", stderr="Internal Server Error")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    exec(source, ns)
    regions = ns["get_subscribed_regions"]()
    
    assert regions == ["ap-tokyo-1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
