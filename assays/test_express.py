"""Tests for express effector script."""
import sys
import subprocess
from pathlib import Path

def test_express_runs_dry_run():
    """Test that express runs with --dry-run without errors."""
    express_path = Path(__file__).parent.parent / "effectors" / "express"
    assert express_path.exists()
    
    # Run with --dry-run
    result = subprocess.run(
        [sys.executable, str(express_path), "--dry-run"],
        capture_output=True,
        text=True
    )
    
    # Check exit code is 0 (success)
    assert result.returncode == 0
    
    # Check that it prints dry run message at the end
    assert "Dry run — no changes made" in result.stdout
    
    # Check that VIVESCA_ROOT is printed correctly
    assert str(Path(__file__).parent.parent) in result.stdout
    
    # Check that existing paths are detected (membrane/cytoskeleton exists)
    assert "OK   ~/.claude/hooks → membrane/cytoskeleton" in result.stdout
    
    # Check that receptors is now found after path fix
    assert "SKIP ~/.claude/skills" not in result.stdout
    assert "~/.claude/skills" in result.stdout
    
    # Check regulatory is still skipped (doesn't exist yet)
    assert "SKIP ~/.claude/rules/* — membrane/regulatory/ not found" in result.stdout

def test_express_paths_correct():
    """Test that all paths in express are correctly defined."""
    # Read the express file to check constants
    express_path = Path(__file__).parent.parent / "effectors" / "express"
    content = express_path.read_text()

    # Check that receptors path is corrected to membrane/receptors
    assert '("~/.claude/skills", "membrane/receptors")' in content
    # Check that original wrong path is not present
    assert '("~/.claude/skills", "receptors")' not in content

    # Check all the required directories exist in the repo
    root = Path(__file__).parent.parent
    cytoskeleton_path = root / "membrane" / "cytoskeleton"
    assert cytoskeleton_path.exists()

    phenotype_path = root / "membrane" / "phenotype.md"
    assert phenotype_path.exists()

    buds_path = root / "membrane" / "buds"
    assert buds_path.exists()
    assert len(list(buds_path.iterdir())) > 0

    receptors_path = root / "membrane" / "receptors"
    assert receptors_path.exists()
    assert len(list(receptors_path.iterdir())) > 10  # Should have many skills
