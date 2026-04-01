from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.resources.anatomy import (
    _extract_decorated_names,
    _extract_module_docstring,
    _extract_module_summary,
    _extract_substrate_info,
    _extract_tool_details,
    _known_lesions,
    _metabolism_modules,
    _metabolism_summary,
    _organ_descriptions,
    _organism_theory,
    _operon_heartbeat,
    _operon_summary,
    _scan_directory,
    _substrate_map,
    express_anatomy,
)


def test_extract_decorated_names_simple():
    """Test extracting decorated function names from AST."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def regular_func():
    pass

@tool
def decorated_func():
    pass

@tool("custom_name")
def another_func():
    pass

@tool(name="named_tool")
def named_func():
    pass
""")
    path = Path(f.name)
    try:
        result = _extract_decorated_names(path, "tool")
        assert len(result) == 3
        names = [r["decorator_arg"] for r in result]
        assert "decorated_func" in names
        assert "custom_name" in names
        assert "named_tool" in names
    finally:
        path.unlink()


def test_extract_decorated_names_empty():
    """Test returns empty list when no decorations match."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(): pass")
    path = Path(f.name)
    try:
        result = _extract_decorated_names(path, "tool")
        assert result == []
    finally:
        path.unlink()


def test_extract_decorated_names_syntax_error():
    """Test returns empty on syntax error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(: pass  # invalid syntax")
    path = Path(f.name)
    try:
        result = _extract_decorated_names(path, "tool")
        assert result == []
    finally:
        path.unlink()


def test_scan_directory_nonexistent():
    """Test scan handles nonexistent directory."""
    result = _scan_directory(Path("/nonexistent/path"), "tool", "test")
    assert len(result) == 1
    assert "no test directory" in result[0]


def test_scan_directory_empty(tmp_path):
    """Test scan handles empty directory."""
    result = _scan_directory(tmp_path, "tool", "test")
    assert len(result) == 1
    assert "no test modules" in result[0]


def test_extract_module_docstring():
    """Test extracting module-level docstring."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module docstring here.\n\nSecond line."""\n')
        f.write("def func(): pass\n")
    path = Path(f.name)
    try:
        result = _extract_module_docstring(path)
        assert result.startswith("Module docstring here")
        assert "Second line" in result
    finally:
        path.unlink()


def test_extract_tool_details():
    """Test extracting tool details including doc and params."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
@tool
def my_tool(param1, param2):
    \"\"\"This is my tool does something.\"\"\"
    pass

@tool(name="custom_tool")
def another(arg):
    \"\"\"Another tool.\"\"\"
    return None
""")
    path = Path(f.name)
    try:
        result = _extract_tool_details(path)
        assert len(result) == 2
        tool = next(t for t in result if t["name"] == "my_tool")
        assert tool["doc"] == "This is my tool does something."
        assert tool["params"] == ["param1", "param2"]

        tool2 = next(t for t in result if t["name"] == "custom_tool")
        assert tool2["doc"] == "Another tool."
        assert tool2["params"] == ["arg"]
    finally:
        path.unlink()


def test_extract_substrate_info():
    """Test extracting substrate class info."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("\"\"\"Cortical substrate for testing.\"\"\"\n")
        f.write("""
class TestSubstrate:
    \"\"\"Test substrate implementation.\"\"\"

    def sense(self):
        \"\"\"Sense the environment.\"\"\"
        pass

    def candidates(self):
        \"\"\"Generate candidates.\"\"\"
        pass

    def act(self):
        \"\"\"Act on the environment.\"\"\"
        pass

    def report(self):
        \"\"\"Report results.\"\"\"
        pass
""")
    path = Path(f.name)
    try:
        result = _extract_substrate_info(path)
        assert result is not None
        assert result["class_name"] == "TestSubstrate"
        assert result["layer"] == "cortical"
        assert set(result["methods"].keys()) == {"sense", "candidates", "act", "report"}
        assert result["methods"]["sense"] == "Sense the environment."
    finally:
        path.unlink()


def test_extract_substrate_info_not_substrate():
    """Test returns None when no Substrate-ending class."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("class Regular: pass")
    path = Path(f.name)
    try:
        result = _extract_substrate_info(path)
        assert result is None
    finally:
        path.unlink()


def test_extract_module_summary():
    """Test extracting module summary."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module summary testing.\"\"\"\n')
        f.write("class TestClass:\n    pass\n")
        f.write("def public_func():\n    pass\n")
        f.write("def _private_func():\n    pass\n")
    path = Path(f.name)
    try:
        result = _extract_module_summary(path)
        assert result is not None
        assert result["first_line"] == "Module summary testing."
        assert "TestClass" in result["classes"]
        assert "public_func" in result["functions"]
        assert "_private_func" not in result["functions"]
    finally:
        path.unlink()


def test_organism_theory(tmp_path):
    """Test extracting theory from DESIGN.md."""
    design = tmp_path / "design.md"
    design.write_text("""
# Project

## The Theory
This is the theory paragraph.
It continues here.

This is another paragraph we shouldn't include.

## The Three Bodies
Three bodies explanation here.
""")
    result = _organism_theory(tmp_path)
    assert len(result) == 2
    assert "**The Theory:** This is the theory paragraph. It continues here." in result


def test_organism_theory_missing(tmp_path):
    """Test handles missing DESIGN.md."""
    result = _organism_theory(tmp_path)
    assert len(result) == 1
    assert "DESIGN.md not found" in result[0]


def test_known_lesions_no_plans(tmp_path):
    """Test known_lesions handles no plans directory."""
    result = _known_lesions(tmp_path)
    assert any("no plans directory" in line for line in result)


@patch("subprocess.run")
def test_known_lesions_subprocess_error(mock_run):
    """Test known_lesions handles subprocess exception."""
    mock_run.side_effect = Exception("Subprocess failed")
    result = _known_lesions(Path("/tmp"))
    assert any("could not run" in line for line in result)


@patch("metabolon.resources.anatomy.subprocess.run")
def test_known_lesions_parses_test_counts(mock_run):
    """Test parsing of pytest test counts."""
    mock_result = MagicMock()
    mock_result.stdout = "2 passed, 1 failed, 0 error"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    result = _known_lesions(Path("/tmp"))
    assert any("2 passed, 1 failed" in line for line in result)


def test_metabolism_summary_import_error():
    """Test metabolism summary handles import error gracefully."""
    with patch.dict("sys.modules", {"metabolon.metabolism.signals": None}):
        result = _metabolism_summary()
        assert any("metabolism data unavailable" in line for line in result)


def test_operon_heartbeat_unavailable():
    """Test operon heartbeat handles exception gracefully."""
    # Mock the import inside the function
    with patch("builtins.__import__", side_effect=ImportError("Not found")):
        result = _operon_heartbeat()
        assert any("operon heartbeat unavailable" in line for line in result)


def test_operon_summary_import_error():
    """Test operon summary handles import gracefully."""
    # Mock the import to raise ImportError
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "metabolon.operons":
            raise ImportError("No module named 'metabolon.operons'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        result = _operon_summary()
        assert any("operon map not found" in line for line in result)


def test_express_anatomy_returns_markdown(tmp_path):
    """Test express_anatomy generates markdown."""
    # Create minimal directory structure
    (tmp_path / "enzymes").mkdir()
    (tmp_path / "resources").mkdir()
    (tmp_path / "codons").mkdir()
    (tmp_path / "metabolism").mkdir()
    (tmp_path / "metabolism" / "substrates").mkdir()

    src_root = tmp_path
    result = express_anatomy(src_root)
    assert isinstance(result, str)
    assert "# vivesca — Anatomy" in result
    assert "Organism Theory" in result
    assert "Known Lesions" in result


def test_organ_descriptions_handles_missing():
    """Test organ descriptions handles missing enzymes directory."""
    result = _organ_descriptions(Path("/nonexistent"))
    assert "_(no enzymes directory)_" == result[0]


def test_substrate_map_handles_missing():
    """Test substrate map handles missing directory."""
    result = _substrate_map(Path("/nonexistent"))
    assert any("_(no substrates directory)_" in line for line in result)


def test_metabolism_modules_handles_missing():
    """Test metabolism modules handles missing directory."""
    result = _metabolism_modules(Path("/nonexistent"))
    assert any("_(no metabolism directory)_" in line for line in result)
