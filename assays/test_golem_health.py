"""Tests for golem-health script."""
import subprocess
import pytest
from pathlib import Path

GOLEM_HEALTH = Path(__file__).parent.parent / "effectors" / "golem-health"

def test_script_exists_and_executable():
    """Test that golem-health exists and is executable."""
    assert GOLEM_HEALTH.exists()
    assert GOLEM_HEALTH.is_file()
    assert GOLEM_HEALTH.stat().st_mode & 0o111 != 0  # has executable bit set

def test_script_help():
    """Test that script can be imported and has docstring."""
    result = subprocess.run(
        [str(GOLEM_HEALTH), "--help"],
        capture_output=True,
        text=True
    )
    # It will exit with non-zero since no --help is implemented
    # but it should print docstring somewhere
    assert result.returncode != 0
    # Check if docstring is present in either stdout or stderr
    output = result.stdout + result.stderr
    assert "golem-health" in output
    assert "Health check" in output

def test_script_importable():
    """Test that the script can be imported as Python module."""
    import sys
    sys.path.insert(0, str(GOLEM_HEALTH.parent))
    try:
        # Just test import works without syntax errors
        import golem_health
        assert hasattr(golem_health, "check_provider")
        assert hasattr(golem_health, "ProviderResult")
        assert hasattr(golem_health, "main")
    finally:
        if "golem_health" in sys.modules:
            del sys.modules["golem_health"]
        sys.path.pop(0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
