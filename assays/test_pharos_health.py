"""Tests for effectors/pharos-health.sh"""
from __future__ import annotations

import subprocess
from pathlib import Path


EFFECTOR = Path.home() / "germline" / "effectors" / "pharos-health.sh"


def test_pharos_health_help_flag():
    """--help shows usage and exits 0."""
    result = subprocess.run(
        [str(EFFECTOR), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "pharos-health.sh" in result.stdout
    assert "disk" in result.stdout.lower()
    assert "memory" in result.stdout.lower()


def test_h_short_flag():
    """-h shows usage and exits 0."""
    result = subprocess.run(
        [str(EFFECTOR), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_health_check_runs():
    """Script runs and exits with valid code (0 or 1)."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    # Exit code should be 0 (healthy) or 1 (unhealthy/alert)
    assert result.returncode in (0, 1)


def test_healthy_output_format():
    """When healthy, output contains expected format."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        # Healthy: stdout should have "ok" and stats
        assert "pharos health:" in result.stdout
        assert "ok" in result.stdout
        assert "disk=" in result.stdout
        assert "mem=" in result.stdout


def test_unhealthy_output_format():
    """When unhealthy, stderr contains alert or tg-notify is called."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 1:
        # Unhealthy: either stderr has alert or tg-notify was called
        output = result.stderr + result.stdout
        # Should have health info somewhere
        assert "pharos health:" in output or "ALERT:" in result.stderr


def test_output_contains_disk_percentage():
    """Output includes disk percentage."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert "disk=" in output
    # Disk should be a number followed by %
    import re
    match = re.search(r"disk=(\d+)%", output)
    assert match is not None
    disk_pct = int(match.group(1))
    assert 0 <= disk_pct <= 100


def test_output_contains_memory_info():
    """Output includes memory info."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert "mem=" in output


def test_output_contains_failed_units():
    """Output includes failed units count."""
    result = subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert "failed_units=" in output
