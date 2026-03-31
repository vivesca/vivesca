"""Comprehensive tests for metabolon/resources/anatomy.py."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

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
    _operon_heartbeat,
    _operon_summary,
    _organ_descriptions,
    _organism_theory,
    _scan_directory,
    _substrate_map,
    express_anatomy,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def sample_tool_module() -> str:
    """Sample Python module with @tool decorators."""
    return '''
"""Sample tool module for testing."""

from some_lib import tool

@tool("my_tool")
def my_function(arg1: str, arg2: int) -> str:
    """A sample tool function.
    
    More details here.
    """
    return arg1

@tool(name="another_tool")
def another_func(x: int) -> int:
    """Another tool."""
    return x

@other_decorator
def not_a_tool():
    pass

@tool
def bare_tool():
    """Bare tool with no args."""
    pass
'''


@pytest.fixture
def sample_resource_module() -> str:
    """Sample Python module with @resource decorators."""
    return '''
"""Sample resource module."""

from some_lib import resource

@resource("my_resource")
def get_data():
    """Get some data."""
    pass

@resource(uri="vivesca://custom")
def custom_uri():
    pass
'''


@pytest.fixture
def sample_substrate_module() -> str:
    """Sample substrate module."""
    return '''
"""Sample substrate module for cortical processing."""

class MyClass:
    """A sample class."""
    pass

class TestSubstrate:
    """Test substrate for cortical layer.

    This handles cortical processing.
    """
    
    def sense(self):
        """Sense the environment."""
        pass
    
    def candidates(self):
        """Get candidates for action."""
        pass
    
    def act(self):
        """Perform the action."""
        pass
    
    def report(self):
        """Report results."""
        pass
    
    def other_method(self):
        """Not part of protocol."""
        pass
'''


@pytest.fixture
def sample_metabolism_module() -> str:
    """Sample metabolism module."""
    return '''
"""Sample metabolism module.

Provides core fitness evaluation.
"""

class FitnessEvaluator:
    """Evaluates fitness scores."""
    pass

class AnotherClass:
    pass

def evaluate_fitness():
    """Evaluate fitness."""
    pass

def _private_func():
    pass
'''


@pytest.fixture
def sample_design_md() -> str:
    """Sample DESIGN.md content."""
    return '''# Design Document

## The Theory

This is the core theory of the organism. It describes how everything works.

More details here.

## The Three Bodies

The three bodies are: physical, digital, and cognitive. They interact in complex ways.

### Subsection

Some additional info.

## The Flywheel, Not The Balance

The flywheel model describes continuous improvement.

```python
# code block that should be ignored
pass
```

## The Body Plan

The body plan defines the structure.

| Column | Value |
|--------|-------|
| A      | B     |

## Metabolism

Metabolism is the core process.

## Two Metabolisms

There are two types: primary and secondary.

## Three Knowledge Artifacts

The three artifacts are: genome, proteome, and metabolome.
'''


@pytest.fixture
def sample_plan_md() -> str:
    """Sample plan with frontmatter."""
    return '''---
status: active
title: "Fix the bug"
---

This plan addresses a critical bug in the system.
'''


@pytest.fixture
def sample_plan_inactive_md() -> str:
    """Sample inactive plan."""
    return '''---
status: completed
title: "Done task"
---

This task is done.
'''


# ── Tests for _extract_decorated_names ───────────────────────────────────


class TestExtractDecoratedNames:
    """Tests for _extract_decorated_names function."""

    def test_extracts_tool_with_string_arg(self, tmp_path: Path, sample_tool_module: str):
        """Test extracting function decorated with @tool("name")."""
        module_path = tmp_path / "test_tool.py"
        module_path.write_text(sample_tool_module)
        
        results = _extract_decorated_names(module_path, "tool")
        
        assert len(results) >= 2
        names = [r["decorator_arg"] for r in results]
        assert "my_tool" in names
        assert "another_tool" in names

    def test_extracts_bare_decorator(self, tmp_path: Path, sample_tool_module: str):
        """Test extracting function with bare @tool decorator."""
        module_path = tmp_path / "test_tool.py"
        module_path.write_text(sample_tool_module)
        
        results = _extract_decorated_names(module_path, "tool")
        
        # bare_tool should use function name as decorator_arg
        bare = next((r for r in results if r["func_name"] == "bare_tool"), None)
        assert bare is not None
        assert bare["decorator_arg"] == "bare_tool"

    def test_ignores_other_decorators(self, tmp_path: Path, sample_tool_module: str):
        """Test that other decorators are ignored."""
        module_path = tmp_path / "test_tool.py"
        module_path.write_text(sample_tool_module)
        
        results = _extract_decorated_names(module_path, "tool")
        
        func_names = [r["func_name"] for r in results]
        assert "not_a_tool" not in func_names

    def test_handles_resource_decorator(self, tmp_path: Path, sample_resource_module: str):
        """Test extracting @resource decorated functions."""
        module_path = tmp_path / "test_resource.py"
        module_path.write_text(sample_resource_module)
        
        results = _extract_decorated_names(module_path, "resource")
        
        assert len(results) == 2
        args = [r["decorator_arg"] for r in results]
        assert "my_resource" in args
        assert "vivesca://custom" in args

    def test_handles_syntax_error(self, tmp_path: Path):
        """Test graceful handling of syntax errors."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def broken(")
        
        results = _extract_decorated_names(module_path, "tool")
        
        assert results == []

    def test_handles_file_not_found(self):
        """Test graceful handling of missing files."""
        results = _extract_decorated_names(Path("/nonexistent/path.py"), "tool")
        
        assert results == []

    def test_handles_attribute_decorator(self, tmp_path: Path):
        """Test handling @module.tool style decorators."""
        code = '''
from some_module import decorators

@decorators.tool("attr_tool")
def my_func():
    pass
'''
        module_path = tmp_path / "attr_dec.py"
        module_path.write_text(code)
        
        results = _extract_decorated_names(module_path, "tool")
        
        assert len(results) == 1
        assert results[0]["decorator_arg"] == "attr_tool"

    def test_handles_async_functions(self, tmp_path: Path):
        """Test handling async functions with decorators."""
        code = '''
@tool("async_tool")
async def async_func():
    """Async tool."""
    pass
'''
        module_path = tmp_path / "async_tool.py"
        module_path.write_text(code)
        
        results = _extract_decorated_names(module_path, "tool")
        
        assert len(results) == 1
        assert results[0]["func_name"] == "async_func"
        assert results[0]["decorator_arg"] == "async_tool"


# ── Tests for _scan_directory ────────────────────────────────────────────


class TestScanDirectory:
    """Tests for _scan_directory function."""

    def test_empty_directory(self, tmp_path: Path):
        """Test scanning empty directory."""
        lines = _scan_directory(tmp_path, "tool", "test")
        
        assert lines == ["  _(no test modules)_"]

    def test_nonexistent_directory(self, tmp_path: Path):
        """Test scanning nonexistent directory."""
        lines = _scan_directory(tmp_path / "nonexistent", "tool", "test")
        
        assert lines == ["  _(no test directory)_"]

    def test_scans_modules(self, tmp_path: Path):
        """Test scanning modules with decorated functions."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        
        (tools_dir / "mod_a.py").write_text('''
@tool("tool_a")
def func_a(): pass
''')
        (tools_dir / "mod_b.py").write_text('''
@tool("tool_b")
def func_b(): pass
@tool("tool_c")
def func_c(): pass
''')
        (tools_dir / "__init__.py").write_text("")
        
        lines = _scan_directory(tools_dir, "tool", "tools")
        
        assert len(lines) == 2
        assert any("mod_a.py" in line and "`tool_a`" in line for line in lines)
        assert any("mod_b.py" in line and "tool_b" in line and "tool_c" in line for line in lines)

    def test_ignores_init_py(self, tmp_path: Path):
        """Test that __init__.py is ignored."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "__init__.py").write_text('@tool("init_tool")\ndef init_func(): pass')
        
        lines = _scan_directory(tools_dir, "tool", "tools")
        
        assert lines == ["  _(no tools modules)_"]

    def test_handles_no_decorators_found(self, tmp_path: Path):
        """Test module with no matching decorators."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "plain.py").write_text("def plain(): pass")
        
        lines = _scan_directory(tools_dir, "tool", "tools")
        
        assert len(lines) == 1
        assert "no @tool found" in lines[0]


# ── Tests for _extract_module_docstring ───────────────────────────────────


class TestExtractModuleDocstring:
    """Tests for _extract_module_docstring function."""

    def test_extracts_docstring(self, tmp_path: Path):
        """Test extracting module docstring."""
        code = '''"""Module docstring here."""

def func(): pass
'''
        module_path = tmp_path / "mod.py"
        module_path.write_text(code)
        
        result = _extract_module_docstring(module_path)
        
        assert result == "Module docstring here."

    def test_no_docstring(self, tmp_path: Path):
        """Test module without docstring."""
        module_path = tmp_path / "mod.py"
        module_path.write_text("def func(): pass")
        
        result = _extract_module_docstring(module_path)
        
        assert result == ""

    def test_syntax_error(self, tmp_path: Path):
        """Test handling syntax error."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def broken(")
        
        result = _extract_module_docstring(module_path)
        
        assert result == ""

    def test_file_not_found(self):
        """Test handling missing file."""
        result = _extract_module_docstring(Path("/nonexistent.py"))
        
        assert result == ""


# ── Tests for _extract_tool_details ───────────────────────────────────────


class TestExtractToolDetails:
    """Tests for _extract_tool_details function."""

    def test_extracts_tool_details(self, tmp_path: Path):
        """Test extracting tool details including docstring and params."""
        code = '''
"""Tool module."""

@tool("my_tool")
def my_func(arg1: str, arg2: int) -> str:
    """First line of docstring.
    
    Additional details.
    """
    pass
'''
        module_path = tmp_path / "tools.py"
        module_path.write_text(code)
        
        results = _extract_tool_details(module_path)
        
        assert len(results) == 1
        assert results[0]["name"] == "my_tool"
        assert results[0]["doc"] == "First line of docstring."
        assert results[0]["params"] == ["arg1", "arg2"]

    def test_excludes_self_param(self, tmp_path: Path):
        """Test that 'self' parameter is excluded."""
        code = '''
class Handler:
    @tool("method_tool")
    def handle(self, data: str):
        """Handle data."""
        pass
'''
        module_path = tmp_path / "handler.py"
        module_path.write_text(code)
        
        results = _extract_tool_details(module_path)
        
        assert len(results) == 1
        assert "self" not in results[0]["params"]
        assert results[0]["params"] == ["data"]

    def test_tool_with_name_kwarg(self, tmp_path: Path):
        """Test tool with name= keyword argument."""
        code = '''
@tool(name="named_tool")
def my_func(x):
    """Named tool."""
    pass
'''
        module_path = tmp_path / "named.py"
        module_path.write_text(code)
        
        results = _extract_tool_details(module_path)
        
        assert len(results) == 1
        assert results[0]["name"] == "named_tool"

    def test_bare_tool_uses_func_name(self, tmp_path: Path):
        """Test bare @tool uses function name."""
        code = '''
@tool
def bare_tool():
    """Bare tool."""
    pass
'''
        module_path = tmp_path / "bare.py"
        module_path.write_text(code)
        
        results = _extract_tool_details(module_path)
        
        assert len(results) == 1
        assert results[0]["name"] == "bare_tool"

    def test_no_docstring(self, tmp_path: Path):
        """Test tool without docstring."""
        code = '''
@tool("no_doc")
def no_doc(x):
    pass
'''
        module_path = tmp_path / "no_doc.py"
        module_path.write_text(code)
        
        results = _extract_tool_details(module_path)
        
        assert len(results) == 1
        assert results[0]["doc"] == ""

    def test_syntax_error(self, tmp_path: Path):
        """Test handling syntax error."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def broken(")
        
        results = _extract_tool_details(module_path)
        
        assert results == []


# ── Tests for _organ_descriptions ─────────────────────────────────────────


class TestOrganDescriptions:
    """Tests for _organ_descriptions function."""

    def test_no_enzymes_directory(self, tmp_path: Path):
        """Test when enzymes directory doesn't exist."""
        lines = _organ_descriptions(tmp_path)
        
        assert lines == ["_(no enzymes directory)_"]

    def test_organ_descriptions(self, tmp_path: Path):
        """Test generating organ descriptions."""
        enzymes_dir = tmp_path / "enzymes"
        enzymes_dir.mkdir()
        
        (enzymes_dir / "tools.py").write_text('''
"""Tools for data processing."""

@tool("process")
def process_data(input: str):
    """Process the input data."""
    pass
''')
        
        lines = _organ_descriptions(tmp_path)
        
        assert any("tools" in line for line in lines)
        assert any("process" in line for line in lines)


# ── Tests for _extract_substrate_info ─────────────────────────────────────


class TestExtractSubstrateInfo:
    """Tests for _extract_substrate_info function."""

    def test_extracts_substrate_info(self, tmp_path: Path, sample_substrate_module: str):
        """Test extracting substrate class info."""
        module_path = tmp_path / "substrate.py"
        module_path.write_text(sample_substrate_module)

        info = _extract_substrate_info(module_path)

        assert info is not None
        assert info["class_name"] == "TestSubstrate"
        # "cortical" is in the module docstring
        assert info["layer"] == "cortical"
        assert "sense" in info["methods"]
        assert "candidates" in info["methods"]

    def test_detects_autonomic_layer(self, tmp_path: Path):
        """Test detecting autonomic layer."""
        code = '''
"""Autonomic processing module."""

class AutoSubstrate:
    """Handles autonomic functions."""
    
    def sense(self):
        """Sense autonomic signals."""
        pass
'''
        module_path = tmp_path / "auto.py"
        module_path.write_text(code)
        
        info = _extract_substrate_info(module_path)
        
        assert info is not None
        assert info["layer"] == "autonomic"

    def test_no_substrate_class(self, tmp_path: Path):
        """Test when no substrate class exists."""
        code = '''
"""Module without substrate."""

class RegularClass:
    pass
'''
        module_path = tmp_path / "no_sub.py"
        module_path.write_text(code)
        
        info = _extract_substrate_info(module_path)
        
        assert info is None

    def test_syntax_error(self, tmp_path: Path):
        """Test handling syntax error."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def broken(")
        
        info = _extract_substrate_info(module_path)
        
        assert info is None


# ── Tests for _substrate_map ──────────────────────────────────────────────


class TestSubstrateMap:
    """Tests for _substrate_map function."""

    def test_no_substrates_directory(self, tmp_path: Path):
        """Test when substrates directory doesn't exist."""
        lines = _substrate_map(tmp_path)
        
        assert lines == ["_(no substrates directory)_"]

    def test_empty_substrates_directory(self, tmp_path: Path):
        """Test empty substrates directory."""
        substrates_dir = tmp_path / "metabolism" / "substrates"
        substrates_dir.mkdir(parents=True)
        
        lines = _substrate_map(tmp_path)
        
        assert lines == ["_(no substrate modules)_"]

    def test_substrate_map(self, tmp_path: Path):
        """Test generating substrate map."""
        substrates_dir = tmp_path / "metabolism" / "substrates"
        substrates_dir.mkdir(parents=True)
        
        (substrates_dir / "test_sub.py").write_text('''
"""Test substrate module."""

class TestSubstrate:
    """Test substrate for cortical layer."""
    
    def sense(self):
        """Sense environment."""
        pass
    
    def candidates(self):
        """Get candidates."""
        pass
    
    def act(self):
        """Act."""
        pass
    
    def report(self):
        """Report."""
        pass
''')
        
        lines = _substrate_map(tmp_path)
        
        assert any("TestSubstrate" in line for line in lines)
        assert any("cortical" in line for line in lines)


# ── Tests for _extract_module_summary ─────────────────────────────────────


class TestExtractModuleSummary:
    """Tests for _extract_module_summary function."""

    def test_extracts_summary(self, tmp_path: Path, sample_metabolism_module: str):
        """Test extracting module summary."""
        module_path = tmp_path / "metabolism.py"
        module_path.write_text(sample_metabolism_module)

        info = _extract_module_summary(module_path)

        assert info is not None
        # The first line of the docstring
        assert "Sample metabolism module" in info["first_line"]
        assert "FitnessEvaluator" in info["classes"]
        assert "AnotherClass" in info["classes"]
        assert "evaluate_fitness" in info["functions"]
        assert "_private_func" not in info["functions"]

    def test_syntax_error(self, tmp_path: Path):
        """Test handling syntax error."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def broken(")

        info = _extract_module_summary(module_path)

        assert info is None


# ── Tests for _metabolism_modules ─────────────────────────────────────────


class TestMetabolismModules:
    """Tests for _metabolism_modules function."""

    def test_no_metabolism_directory(self, tmp_path: Path):
        """Test when metabolism directory doesn't exist."""
        lines = _metabolism_modules(tmp_path)
        
        assert lines == ["_(no metabolism directory)_"]

    def test_empty_metabolism_directory(self, tmp_path: Path):
        """Test empty metabolism directory."""
        met_dir = tmp_path / "metabolism"
        met_dir.mkdir()
        
        lines = _metabolism_modules(tmp_path)
        
        assert lines == ["_(no metabolism modules)_"]

    def test_metabolism_modules(self, tmp_path: Path):
        """Test generating metabolism modules summary."""
        met_dir = tmp_path / "metabolism"
        met_dir.mkdir()
        
        (met_dir / "fitness.py").write_text('''
"""Fitness evaluation module."""

class Evaluator:
    pass

def evaluate():
    pass
''')
        (met_dir / "__init__.py").write_text("")
        
        lines = _metabolism_modules(tmp_path)
        
        assert any("fitness" in line.lower() for line in lines)
        assert any("Evaluator" in line for line in lines)


# ── Tests for _metabolism_summary ─────────────────────────────────────────


class TestMetabolismSummary:
    """Tests for _metabolism_summary function."""

    @patch("metabolon.metabolism.variants.Genome")
    @patch("metabolon.metabolism.signals.SensorySystem")
    def test_summary_success(self, mock_sensory: Mock, mock_genome: Mock):
        """Test successful metabolism summary."""
        # Setup mock genome
        genome_instance = MagicMock()
        genome_instance.expressed_tools.return_value = ["tool1", "tool2"]
        genome_instance.allele_variants.side_effect = lambda t: [f"{t}_v1", f"{t}_v2"]
        mock_genome.return_value = genome_instance

        # Setup mock sensory system
        sensory_instance = MagicMock()
        signal1 = MagicMock(tool="tool1")
        signal2 = MagicMock(tool="tool1")
        signal3 = MagicMock(tool="tool2")
        sensory_instance.recall_since.return_value = [signal1, signal2, signal3]
        mock_sensory.return_value = sensory_instance

        lines = _metabolism_summary()

        # Output uses **N** markdown bold format
        assert any("**2** tool(s)" in line for line in lines)
        assert any("**4** total variant(s)" in line for line in lines)
        assert any("**3**" in line and "7 days" in line for line in lines)

    @patch("metabolon.metabolism.variants.Genome", side_effect=ImportError)
    def test_summary_import_error(self, mock_genome: Mock):
        """Test handling import error gracefully."""
        lines = _metabolism_summary()

        assert any("unavailable" in line for line in lines)

    @patch("metabolon.metabolism.variants.Genome", side_effect=Exception("boom"))
    def test_summary_exception(self, mock_genome: Mock):
        """Test handling general exception gracefully."""
        lines = _metabolism_summary()

        assert any("unavailable" in line for line in lines)


# ── Tests for _organism_theory ────────────────────────────────────────────


class TestOrganismTheory:
    """Tests for _organism_theory function."""

    def test_no_design_md(self, tmp_path: Path):
        """Test when design.md doesn't exist."""
        lines = _organism_theory(tmp_path)
        
        assert lines == ["_(DESIGN.md not found)_"]

    def test_unreadable_design_md(self, tmp_path: Path):
        """Test handling unreadable design.md."""
        design_path = tmp_path / "design.md"
        design_path.mkdir()  # Make it a directory to trigger OSError
        
        lines = _organism_theory(tmp_path)
        
        assert any("unreadable" in line.lower() for line in lines)

    def test_extracts_theory(self, tmp_path: Path, sample_design_md: str):
        """Test extracting theory sections."""
        design_path = tmp_path / "design.md"
        design_path.write_text(sample_design_md)
        
        lines = _organism_theory(tmp_path)
        
        # Should extract section summaries
        assert any("Theory" in line for line in lines)
        assert any("Three Bodies" in line for line in lines)

    def test_ignores_code_blocks(self, tmp_path: Path):
        """Test that code blocks are ignored in summaries."""
        # Use a heading that's in section_keys
        design = '''## The Theory

First paragraph here.

```python
code here
```

Second paragraph.
'''
        design_path = tmp_path / "design.md"
        design_path.write_text(design)

        lines = _organism_theory(tmp_path)

        # Should only get first paragraph
        assert any("First paragraph" in line for line in lines)
        assert not any("Second paragraph" in line for line in lines)

    def test_ignores_tables(self, tmp_path: Path):
        """Test that tables are ignored in summaries."""
        # Use a heading that's in section_keys
        design = '''## The Theory

First paragraph here.

| A | B |
|---|---|
| 1 | 2 |

Second paragraph.
'''
        design_path = tmp_path / "design.md"
        design_path.write_text(design)

        lines = _organism_theory(tmp_path)

        assert any("First paragraph" in line for line in lines)
        assert not any("Second paragraph" in line for line in lines)


# ── Tests for _known_lesions ──────────────────────────────────────────────


class TestKnownLesions:
    """Tests for _known_lesions function."""

    def test_no_plans_directory(self, tmp_path: Path):
        """Test when plans directory doesn't exist."""
        lines = _known_lesions(tmp_path)
        
        assert any("no plans directory" in line for line in lines)

    def test_no_active_plans(self, tmp_path: Path):
        """Test when there are no active plans."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        
        (plans_dir / "done.md").write_text('''---
status: completed
title: "Done"
---

Done task.
''')
        
        lines = _known_lesions(tmp_path)
        
        assert any("no active plans" in line for line in lines)

    def test_active_plans(self, tmp_path: Path):
        """Test with active plans."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        
        (plans_dir / "active.md").write_text('''---
status: active
title: "Active Task"
---

This is an active plan.
''')
        
        with patch("metabolon.resources.anatomy.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="5 passed", stderr="")
            lines = _known_lesions(tmp_path)
        
        assert any("Active Task" in line for line in lines)

    def test_test_results_healthy(self, tmp_path: Path):
        """Test healthy test results."""
        with patch("metabolon.resources.anatomy.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="10 passed in 1.0s",
                stderr=""
            )
            lines = _known_lesions(tmp_path)
        
        assert any("healthy" in line.lower() for line in lines)
        assert any("10 passed" in line for line in lines)

    def test_test_results_unhealthy(self, tmp_path: Path):
        """Test unhealthy test results."""
        with patch("metabolon.resources.anatomy.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="8 passed, 2 failed, 1 error",
                stderr=""
            )
            lines = _known_lesions(tmp_path)
        
        assert any("UNHEALTHY" in line for line in lines)

    def test_test_results_exception(self, tmp_path: Path):
        """Test handling test run exception."""
        with patch("metabolon.resources.anatomy.subprocess.run", side_effect=Exception("boom")):
            lines = _known_lesions(tmp_path)
        
        assert any("could not run" in line for line in lines)

    def test_malformed_frontmatter(self, tmp_path: Path):
        """Test handling malformed frontmatter."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        
        (plans_dir / "bad.md").write_text('''---
title: "Missing Status"
---

No status field.
''')
        
        with patch("metabolon.resources.anatomy.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            lines = _known_lesions(tmp_path)
        
        assert any("no active plans" in line for line in lines)


# ── Tests for _operon_heartbeat ───────────────────────────────────────────


class TestOperonHeartbeat:
    """Tests for _operon_heartbeat function."""

    @patch("metabolon.metabolism.substrates.operons.OperonSubstrate")
    def test_heartbeat_success(self, mock_substrate: Mock):
        """Test successful operon heartbeat."""
        substrate_instance = MagicMock()
        substrate_instance.sense.return_value = [
            {"reaction": "healthy_op", "stale": False, "days_since": 1, "cadence_days": 7},
            {"reaction": "stale_op", "stale": True, "days_since": 30, "cadence_days": 7},
        ]
        mock_substrate.return_value = substrate_instance

        lines = _operon_heartbeat()

        # Output uses **N** markdown bold format
        assert any("**1** healthy" in line for line in lines)
        assert any("**1** stale" in line for line in lines)
        assert any("stale_op" in line for line in lines)

    @patch("metabolon.metabolism.substrates.operons.OperonSubstrate", side_effect=ImportError)
    def test_heartbeat_import_error(self, mock_substrate: Mock):
        """Test handling import error."""
        lines = _operon_heartbeat()

        assert any("unavailable" in line for line in lines)

    @patch("metabolon.metabolism.substrates.operons.OperonSubstrate", side_effect=Exception("boom"))
    def test_heartbeat_exception(self, mock_substrate: Mock):
        """Test handling general exception."""
        lines = _operon_heartbeat()

        assert any("unavailable" in line for line in lines)

    @patch("metabolon.metabolism.substrates.operons.OperonSubstrate")
    def test_heartbeat_never_fired(self, mock_substrate: Mock):
        """Test operon that has never fired."""
        substrate_instance = MagicMock()
        substrate_instance.sense.return_value = [
            {"reaction": "never_fired", "stale": True, "days_since": None, "cadence_days": 7},
        ]
        mock_substrate.return_value = substrate_instance

        lines = _operon_heartbeat()

        assert any("never fired" in line for line in lines)


# ── Tests for _operon_summary ─────────────────────────────────────────────


class TestOperonSummary:
    """Tests for _operon_summary function."""

    def test_operon_summary(self):
        """Test operon summary generation."""
        op1 = MagicMock(
            reaction="op1",
            expressed=True,
            precipitation="active",
            product="Product 1",
            enzymes=["tool1", "tool2"],
        )
        op2 = MagicMock(
            reaction="op2",
            expressed=False,
            precipitation="dormant",
            product="Product 2",
            enzymes=[],
        )
        op3 = MagicMock(
            reaction="op3",
            expressed=True,
            precipitation="crystallised",
            product="Product 3",
            enzymes=["tool3"],
        )
        operon_list = [op1, op2, op3]

        with patch("metabolon.operons.OPERONS", operon_list):
            lines = _operon_summary()

        assert any("op1" in line for line in lines)
        assert any("op2" in line for line in lines)
        # Output uses **N** markdown bold format
        assert any("operons" in line and "3" in line for line in lines)
        assert any("2 active" in line for line in lines)
        assert any("1 dormant" in line for line in lines)
        assert any("1 crystallised" in line for line in lines)

    def test_operon_summary_import_error(self):
        """Test handling import error."""
        # Simulate ImportError by patching the module to raise on import
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "metabolon.operons":
                raise ImportError("mocked")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            lines = _operon_summary()

        assert any("not found" in line for line in lines)


# ── Tests for express_anatomy ─────────────────────────────────────────────


class TestExpressAnatomy:
    """Tests for the main express_anatomy function."""

    def test_express_anatomy_basic(self, tmp_path: Path):
        """Test basic anatomy generation."""
        # Create minimal directory structure
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "__init__.py").write_text("")
        
        # Create resources directory
        resources = metabolon / "resources"
        resources.mkdir()
        (resources / "__init__.py").write_text("")
        
        result = express_anatomy(metabolon)
        
        assert "# vivesca — Anatomy" in result
        assert "## Organism Theory" in result
        assert "## Registered Tools" in result
        assert "## Registered Resources" in result

    def test_express_anatomy_with_tools(self, tmp_path: Path):
        """Test anatomy generation with tools."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        
        enzymes = metabolon / "enzymes"
        enzymes.mkdir()
        (enzymes / "my_tools.py").write_text('''
"""My tools module."""

@tool("my_tool")
def my_func(x: int) -> int:
    """A tool."""
    return x
''')
        
        result = express_anatomy(metabolon)
        
        assert "## Organ Descriptions" in result
        assert "my_tools" in result

    def test_express_anatomy_uses_default_src(self):
        """Test that express_anatomy uses default src when None provided."""
        with patch("metabolon.resources.anatomy._organism_theory") as mock_theory, \
             patch("metabolon.resources.anatomy._organ_descriptions") as mock_organs, \
             patch("metabolon.resources.anatomy._substrate_map") as mock_substrate, \
             patch("metabolon.resources.anatomy._metabolism_modules") as mock_met, \
             patch("metabolon.resources.anatomy._scan_directory") as mock_scan, \
             patch("metabolon.resources.anatomy._operon_summary") as mock_operon, \
             patch("metabolon.resources.anatomy._operon_heartbeat") as mock_heartbeat, \
             patch("metabolon.resources.anatomy._metabolism_summary") as mock_met_sum, \
             patch("metabolon.resources.anatomy._known_lesions") as mock_lesions:
            
            mock_theory.return_value = []
            mock_organs.return_value = []
            mock_substrate.return_value = []
            mock_met.return_value = []
            mock_scan.return_value = []
            mock_operon.return_value = []
            mock_heartbeat.return_value = []
            mock_met_sum.return_value = []
            mock_lesions.return_value = []
            
            result = express_anatomy()
            
            assert "vivesca — Anatomy" in result


# ── Integration-style tests ───────────────────────────────────────────────


class TestEdgeCases:
    """Additional edge case tests."""

    def test_empty_file(self, tmp_path: Path):
        """Test handling empty file."""
        module_path = tmp_path / "empty.py"
        module_path.write_text("")
        
        assert _extract_decorated_names(module_path, "tool") == []
        assert _extract_module_docstring(module_path) == ""
        assert _extract_tool_details(module_path) == []
        assert _extract_substrate_info(module_path) is None

    def test_unicode_in_docstring(self, tmp_path: Path):
        """Test handling unicode in docstrings."""
        code = '''
"""Module with émojis 🎉 and unicode."""

@tool("unicode_tool")
def func():
    """Function with 中文 characters."""
    pass
'''
        module_path = tmp_path / "unicode.py"
        module_path.write_text(code)
        
        docstring = _extract_module_docstring(module_path)
        assert "émojis" in docstring
        
        details = _extract_tool_details(module_path)
        assert len(details) == 1
        assert "中文" in details[0]["doc"]

    def test_multiline_decorator(self, tmp_path: Path):
        """Test handling multiline decorators."""
        code = '''
@tool(
    "multiline_tool",
    description="A tool with many args"
)
def func():
    pass
'''
        module_path = tmp_path / "multiline.py"
        module_path.write_text(code)
        
        results = _extract_decorated_names(module_path, "tool")
        
        assert len(results) == 1
        assert results[0]["decorator_arg"] == "multiline_tool"

    def test_nested_class_substrate(self, tmp_path: Path):
        """Test handling nested classes."""
        code = '''
class Outer:
    class InnerSubstrate:
        """Nested substrate."""
        
        def sense(self):
            pass
'''
        module_path = tmp_path / "nested.py"
        module_path.write_text(code)
        
        info = _extract_substrate_info(module_path)
        
        # Should find InnerSubstrate
        assert info is not None
        assert info["class_name"] == "InnerSubstrate"

    def test_plan_with_multiline_body(self, tmp_path: Path):
        """Test plan with multiline body."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        
        (plans_dir / "complex.md").write_text('''---
status: active
title: "Complex Plan"
---

# Overview

This is a complex plan with multiple sections.

## Details

More details here.
''')
        
        with patch("metabolon.resources.anatomy.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            lines = _known_lesions(tmp_path)
        
        assert any("Complex Plan" in line for line in lines)
