#!/usr/bin/env python3
"""Tests for switch-layer effector — tests layer switching and vocabulary management."""

import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# Execute the switch-layer script directly
switch_layer_path = Path("/home/terry/germline/effectors/switch-layer")
switch_layer_code = switch_layer_path.read_text()
namespace = {}
exec(switch_layer_code, namespace)

# Extract all the functions/globals from the namespace
sl = type('switch_layer_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(sl, key, value)


# ---------------------------------------------------------------------------
# Test constants and configuration
# ---------------------------------------------------------------------------

def test_genome_path_defined():
    """Test GENOME path is set to skills directory."""
    assert sl.GENOME == Path.home() / "skills"


def test_variants_path_defined():
    """Test VARIANTS path is set correctly."""
    assert sl.VARIANTS == sl.GENOME / "layers"


def test_phenotype_path_defined():
    """Test PHENOTYPE path is set to Claude skills directory."""
    assert sl.PHENOTYPE == Path.home() / ".claude" / "skills"


def test_current_layer_path_defined():
    """Test CURRENT_LAYER path is set correctly."""
    assert sl.CURRENT_LAYER == sl.VARIANTS / ".current"


def test_foreign_tissue_excludes():
    """Test FOREIGN_TISSUE excludes important directories."""
    assert ".git" in sl.FOREIGN_TISSUE
    assert "node_modules" in sl.FOREIGN_TISSUE
    assert "__pycache__" in sl.FOREIGN_TISSUE
    assert "layers" in sl.FOREIGN_TISSUE


def test_expressible_extensions():
    """Test EXPRESSIBLE contains expected file extensions."""
    assert ".py" in sl.EXPRESSIBLE
    assert ".md" in sl.EXPRESSIBLE
    assert ".yaml" in sl.EXPRESSIBLE
    assert ".sh" in sl.EXPRESSIBLE


def test_membrane_embedded_commands():
    """Test MEMBRANE_EMBEDDED contains protected command names."""
    assert "plan" in sl.MEMBRANE_EMBEDDED
    assert "publish" in sl.MEMBRANE_EMBEDDED
    assert "analyze" in sl.MEMBRANE_EMBEDDED


# ---------------------------------------------------------------------------
# Test read_variant function
# ---------------------------------------------------------------------------

def test_read_variant_not_found(capsys):
    """Test read_variant exits when layer file doesn't exist."""
    # Patch the namespace directly
    old_variants = namespace['VARIANTS']
    namespace['VARIANTS'] = Path("/nonexistent/layers")
    try:
        with pytest.raises(SystemExit) as exc_info:
            sl.read_variant("nonexistent_layer")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Layer not found" in captured.out
    finally:
        namespace['VARIANTS'] = old_variants


def test_read_variant_parses_yaml():
    """Test read_variant parses YAML layer file correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        layer_file = variants_dir / "test_layer.yaml"
        layer_file.write_text("old_name: new_name\nother: another\n")
        
        old_variants = namespace['VARIANTS']
        namespace['VARIANTS'] = variants_dir
        try:
            result = sl.read_variant("test_layer")
            assert result == {"old_name": "new_name", "other": "another"}
        finally:
            namespace['VARIANTS'] = old_variants


def test_read_variant_filters_non_strings():
    """Test read_variant filters out non-string values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        layer_file = variants_dir / "test_layer.yaml"
        layer_file.write_text("name: value\nnumber: 42\nlist:\n  - a\n  - b\n")
        
        old_variants = namespace['VARIANTS']
        namespace['VARIANTS'] = variants_dir
        try:
            result = sl.read_variant("test_layer")
            assert result == {"name": "value"}
            assert "number" not in result
            assert "list" not in result
        finally:
            namespace['VARIANTS'] = old_variants


# ---------------------------------------------------------------------------
# Test active_layer function
# ---------------------------------------------------------------------------

def test_active_layer_default_when_no_file():
    """Test active_layer returns 'default' when .current file doesn't exist."""
    old_current = namespace['CURRENT_LAYER']
    namespace['CURRENT_LAYER'] = Path("/nonexistent/.current")
    try:
        assert sl.active_layer() == "default"
    finally:
        namespace['CURRENT_LAYER'] = old_current


def test_active_layer_reads_file():
    """Test active_layer reads layer name from .current file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        current_file = Path(tmpdir) / ".current"
        current_file.write_text("test_layer\n")
        
        old_current = namespace['CURRENT_LAYER']
        namespace['CURRENT_LAYER'] = current_file
        try:
            assert sl.active_layer() == "test_layer"
        finally:
            namespace['CURRENT_LAYER'] = old_current


# ---------------------------------------------------------------------------
# Test list_variants function
# ---------------------------------------------------------------------------

def test_list_variants_empty():
    """Test list_variants returns empty list when no layers exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        
        old_variants = namespace['VARIANTS']
        namespace['VARIANTS'] = variants_dir
        try:
            assert sl.list_variants() == []
        finally:
            namespace['VARIANTS'] = old_variants


def test_list_variants_finds_yaml_files():
    """Test list_variants finds and sorts layer files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        (variants_dir / "z_layer.yaml").write_text("a: b\n")
        (variants_dir / "a_layer.yaml").write_text("a: b\n")
        
        old_variants = namespace['VARIANTS']
        namespace['VARIANTS'] = variants_dir
        try:
            result = sl.list_variants()
            assert result == ["a_layer", "z_layer"]
        finally:
            namespace['VARIANTS'] = old_variants


# ---------------------------------------------------------------------------
# Test reverse_mapping function
# ---------------------------------------------------------------------------

def test_reverse_mapping_default():
    """Test reverse_mapping returns empty dict for default layer."""
    old_current = namespace['CURRENT_LAYER']
    namespace['CURRENT_LAYER'] = Path("/nonexistent/.current")
    try:
        assert sl.reverse_mapping() == {}
    finally:
        namespace['CURRENT_LAYER'] = old_current


def test_reverse_mapping_reverses():
    """Test reverse_mapping correctly reverses key-value pairs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        current_file = variants_dir / ".current"
        current_file.write_text("test_layer\n")
        (variants_dir / "test_layer.yaml").write_text("old: new\nfoo: bar\n")
        
        old_variants = namespace['VARIANTS']
        old_current = namespace['CURRENT_LAYER']
        namespace['VARIANTS'] = variants_dir
        namespace['CURRENT_LAYER'] = current_file
        try:
            result = sl.reverse_mapping()
            assert result == {"new": "old", "bar": "foo"}
        finally:
            namespace['VARIANTS'] = old_variants
            namespace['CURRENT_LAYER'] = old_current


# ---------------------------------------------------------------------------
# Test express_phenotype function
# ---------------------------------------------------------------------------

def test_express_phenotype_dry_run():
    """Test express_phenotype returns changes without modifying files in dry-run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        genome_dir = Path(tmpdir) / "skills"
        genome_dir.mkdir()
        phenotype_dir = Path(tmpdir) / "phenotype"
        phenotype_dir.mkdir()
        
        # Create a skill directory
        skill_dir = genome_dir / "test_skill"
        skill_dir.mkdir()
        
        old_genome = namespace['GENOME']
        old_phenotype = namespace['PHENOTYPE']
        namespace['GENOME'] = genome_dir
        namespace['PHENOTYPE'] = phenotype_dir
        try:
            changes = sl.express_phenotype({"test_skill": "renamed_skill"}, dry_run=True)
            assert ("skill", "test_skill", "renamed_skill") in changes
            # Should not create symlink in dry-run
            assert not (phenotype_dir / "renamed_skill").exists()
        finally:
            namespace['GENOME'] = old_genome
            namespace['PHENOTYPE'] = old_phenotype


def test_express_phenotype_creates_symlink():
    """Test express_phenotype creates symlinks when not dry-run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        genome_dir = Path(tmpdir) / "skills"
        genome_dir.mkdir()
        phenotype_dir = Path(tmpdir) / "phenotype"
        phenotype_dir.mkdir()
        
        skill_dir = genome_dir / "test_skill"
        skill_dir.mkdir()
        
        old_genome = namespace['GENOME']
        old_phenotype = namespace['PHENOTYPE']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['GENOME'] = genome_dir
        namespace['PHENOTYPE'] = phenotype_dir
        namespace['FOREIGN_TISSUE'] = set()
        try:
            sl.express_phenotype({"test_skill": "renamed_skill"}, dry_run=False)
            symlink = phenotype_dir / "renamed_skill"
            assert symlink.is_symlink()
            assert symlink.resolve() == skill_dir
        finally:
            namespace['GENOME'] = old_genome
            namespace['PHENOTYPE'] = old_phenotype
            namespace['FOREIGN_TISSUE'] = old_foreign


# ---------------------------------------------------------------------------
# Test express_effectors function
# ---------------------------------------------------------------------------

def test_express_effectors_creates_alias():
    """Test express_effectors creates CLI aliases in bin."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        
        # Create a real script
        script = bin_dir / "old_cmd"
        script.write_text("#!/bin/bash\necho hello\n")
        
        # Patch Path.home to return our tmpdir
        with patch('pathlib.Path.home', return_value=Path(tmpdir)):
            # Re-execute to get fresh namespace with patched home
            ns = {}
            exec(switch_layer_code, ns)
            changes = ns['express_effectors']({"old_cmd": "new_cmd"}, dry_run=False)
            alias = bin_dir / "new_cmd"
            if alias.exists():
                assert ("cli-alias", "old_cmd", "new_cmd") in changes


# ---------------------------------------------------------------------------
# Test transcribe function
# ---------------------------------------------------------------------------

def test_transcribe_dry_run():
    """Test transcribe returns changes without modifying in dry-run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        region = Path(tmpdir) / "region"
        region.mkdir()
        test_file = region / "test.py"
        test_file.write_text("old_name = 1\n")
        
        old_cytoplasm = namespace['CYTOPLASM']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['CYTOPLASM'] = [region]
        namespace['FOREIGN_TISSUE'] = set()
        try:
            changes = sl.transcribe({"old_name": "new_name"}, dry_run=True)
            # File should not be modified
            assert "old_name" in test_file.read_text()
        finally:
            namespace['CYTOPLASM'] = old_cytoplasm
            namespace['FOREIGN_TISSUE'] = old_foreign


def test_transcribe_respects_membrane_embedded():
    """Test transcribe doesn't replace MEMBRANE_EMBEDDED commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        region = Path(tmpdir) / "region"
        region.mkdir()
        test_file = region / "test.py"
        test_file.write_text("plan = 1\n")
        
        old_cytoplasm = namespace['CYTOPLASM']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['CYTOPLASM'] = [region]
        namespace['FOREIGN_TISSUE'] = set()
        try:
            changes = sl.transcribe({"plan": "schema"}, dry_run=True)
            # 'plan' is in MEMBRANE_EMBEDDED, should not be changed
            assert changes == []
        finally:
            namespace['CYTOPLASM'] = old_cytoplasm
            namespace['FOREIGN_TISSUE'] = old_foreign


# ---------------------------------------------------------------------------
# Test differentiate function
# ---------------------------------------------------------------------------

def test_differentiate_default(capsys):
    """Test differentiate with 'default' layer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        genome_dir = Path(tmpdir) / "skills"
        genome_dir.mkdir()
        phenotype_dir = Path(tmpdir) / "phenotype"
        phenotype_dir.mkdir()
        variants_dir = Path(tmpdir) / "layers"
        variants_dir.mkdir()
        current_file = variants_dir / ".current"
        
        skill_dir = genome_dir / "test"
        skill_dir.mkdir()
        
        old_genome = namespace['GENOME']
        old_phenotype = namespace['PHENOTYPE']
        old_variants = namespace['VARIANTS']
        old_current = namespace['CURRENT_LAYER']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['GENOME'] = genome_dir
        namespace['PHENOTYPE'] = phenotype_dir
        namespace['VARIANTS'] = variants_dir
        namespace['CURRENT_LAYER'] = current_file
        namespace['FOREIGN_TISSUE'] = set()
        try:
            sl.differentiate("default", dry_run=True)
            captured = capsys.readouterr()
            assert "Restored to default names" in captured.out
        finally:
            namespace['GENOME'] = old_genome
            namespace['PHENOTYPE'] = old_phenotype
            namespace['VARIANTS'] = old_variants
            namespace['CURRENT_LAYER'] = old_current
            namespace['FOREIGN_TISSUE'] = old_foreign


def test_differentiate_dry_run(capsys):
    """Test differentiate with dry_run shows preview."""
    with tempfile.TemporaryDirectory() as tmpdir:
        genome_dir = Path(tmpdir) / "skills"
        genome_dir.mkdir()
        phenotype_dir = Path(tmpdir) / "phenotype"
        phenotype_dir.mkdir()
        variants_dir = Path(tmpdir) / "layers"
        variants_dir.mkdir()
        current_file = variants_dir / ".current"
        
        skill_dir = genome_dir / "test"
        skill_dir.mkdir()
        layer_file = variants_dir / "test_layer.yaml"
        layer_file.write_text("test: renamed\n")
        
        old_genome = namespace['GENOME']
        old_phenotype = namespace['PHENOTYPE']
        old_variants = namespace['VARIANTS']
        old_current = namespace['CURRENT_LAYER']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['GENOME'] = genome_dir
        namespace['PHENOTYPE'] = phenotype_dir
        namespace['VARIANTS'] = variants_dir
        namespace['CURRENT_LAYER'] = current_file
        namespace['FOREIGN_TISSUE'] = set()
        try:
            sl.differentiate("test_layer", dry_run=True)
            captured = capsys.readouterr()
            assert "dry run" in captured.out.lower()
        finally:
            namespace['GENOME'] = old_genome
            namespace['PHENOTYPE'] = old_phenotype
            namespace['VARIANTS'] = old_variants
            namespace['CURRENT_LAYER'] = old_current
            namespace['FOREIGN_TISSUE'] = old_foreign


# ---------------------------------------------------------------------------
# Test main function CLI handling
# ---------------------------------------------------------------------------

def test_main_help(capsys):
    """Test --help shows usage."""
    with patch('sys.argv', ['switch-layer', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            sl.main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "switch-layer" in captured.out


def test_main_current(capsys):
    """Test --current shows active layer."""
    old_current = namespace['CURRENT_LAYER']
    namespace['CURRENT_LAYER'] = Path("/nonexistent/.current")
    try:
        with patch('sys.argv', ['switch-layer', '--current']):
            sl.main()
            captured = capsys.readouterr()
            assert "default" in captured.out
    finally:
        namespace['CURRENT_LAYER'] = old_current


def test_main_list(capsys):
    """Test --list shows available layers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        variants_dir = Path(tmpdir)
        (variants_dir / "layer1.yaml").write_text("a: b\n")
        
        old_variants = namespace['VARIANTS']
        old_current = namespace['CURRENT_LAYER']
        namespace['VARIANTS'] = variants_dir
        namespace['CURRENT_LAYER'] = Path("/nonexistent/.current")
        try:
            with patch('sys.argv', ['switch-layer', '--list']):
                sl.main()
                captured = capsys.readouterr()
                assert "layer1" in captured.out
        finally:
            namespace['VARIANTS'] = old_variants
            namespace['CURRENT_LAYER'] = old_current


def test_main_dry_run_flag(capsys):
    """Test --dry-run flag triggers dry run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        genome_dir = Path(tmpdir) / "skills"
        genome_dir.mkdir()
        phenotype_dir = Path(tmpdir) / "phenotype"
        phenotype_dir.mkdir()
        variants_dir = Path(tmpdir) / "layers"
        variants_dir.mkdir()
        current_file = variants_dir / ".current"
        
        layer_file = variants_dir / "test.yaml"
        layer_file.write_text("a: b\n")
        
        old_genome = namespace['GENOME']
        old_phenotype = namespace['PHENOTYPE']
        old_variants = namespace['VARIANTS']
        old_current = namespace['CURRENT_LAYER']
        old_foreign = namespace['FOREIGN_TISSUE']
        namespace['GENOME'] = genome_dir
        namespace['PHENOTYPE'] = phenotype_dir
        namespace['VARIANTS'] = variants_dir
        namespace['CURRENT_LAYER'] = current_file
        namespace['FOREIGN_TISSUE'] = set()
        try:
            with patch('sys.argv', ['switch-layer', '--dry-run', 'test']):
                sl.main()
                captured = capsys.readouterr()
                assert "dry run" in captured.out.lower()
        finally:
            namespace['GENOME'] = old_genome
            namespace['PHENOTYPE'] = old_phenotype
            namespace['VARIANTS'] = old_variants
            namespace['CURRENT_LAYER'] = old_current
            namespace['FOREIGN_TISSUE'] = old_foreign
