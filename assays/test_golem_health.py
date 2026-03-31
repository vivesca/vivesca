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

def test_script_has_correct_permissions():
    """Test permissions are correct."""
    assert oct(GOLEM_HEALTH.stat().st_mode)[-3:] == "755"

def test_script_contains_expected_providers():
    """Test that all expected providers are in the script."""
    content = GOLEM_HEALTH.read_text()
    assert "zhipu" in content
    assert "infini" in content
    assert "volcano" in content
    assert "check_provider" in content
    assert "ProviderResult" in content

def test_script_importable():
    """Test that the script has no syntax errors when run with python."""
    # Check syntax by running with -c import
    result = subprocess.run(
        ["python3", "-c", f"import ast; ast.parse(open('{GOLEM_HEALTH}').read())"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0  # no syntax errors

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
