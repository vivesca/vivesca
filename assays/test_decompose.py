"""Tests for metabolon.sortase.decompose module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from metabolon.sortase.decompose import (
    ComplexityScore,
    TaskSpec,
    _strip_fences,
    _parse_yaml_tasks,
    estimate_complexity,
    score_spec_quality,
    lint_plan,
    decompose_plan,
)


class TestComplexityScore:
    """Tests for ComplexityScore dataclass."""

    def test_frozen_dataclass(self):
        """ComplexityScore is immutable."""
        score = ComplexityScore(
            level="simple",
            files_referenced=1,
            code_blocks=0,
            verification_commands=0,
            estimated_lines=10,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            score.level = "complex"

    def test_all_fields_present(self):
        """All expected fields are present."""
        score = ComplexityScore(
            level="medium",
            files_referenced=2,
            code_blocks=3,
            verification_commands=1,
            estimated_lines=50,
        )
        assert score.level == "medium"
        assert score.files_referenced == 2
        assert score.code_blocks == 3
        assert score.verification_commands == 1
        assert score.estimated_lines == 50


class TestTaskSpec:
    """Tests for TaskSpec dataclass."""

    def test_default_values(self):
        """Default values for optional fields."""
        spec = TaskSpec(
            name="test",
            description="Test task",
            spec="Do something",
            files=["file1.py"],
        )
        assert spec.signal == "default"
        assert spec.prerequisite is None
        assert spec.temp_file is None

    def test_frozen_dataclass(self):
        """TaskSpec is immutable."""
        spec = TaskSpec(
            name="test",
            description="Test",
            spec="Do something",
            files=[],
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            spec.name = "other"


class TestStripFences:
    """Tests for _strip_fences function."""

    def test_removes_yaml_fences(self):
        """YAML fences are removed."""
        text = "```yaml\nkey: value\n```"
        result = _strip_fences(text)
        assert "```" not in result
        assert "key: value" in result

    def test_removes_plain_fences(self):
        """Plain fences are removed."""
        text = "```\ncode here\n```"
        result = _strip_fences(text)
        assert "```" not in result

    def test_preserves_content_without_fences(self):
        """Content without fences is preserved."""
        text = "plain text content"
        result = _strip_fences(text)
        assert result == text


class TestParseYamlTasks:
    """Tests for _parse_yaml_tasks function."""

    def test_parse_list_of_tasks(self):
        """Parse YAML list of tasks."""
        yaml_text = """
- name: task1
  description: First task
  files: [file1.py]
- name: task2
  description: Second task
  files: [file2.py]
"""
        tasks = _parse_yaml_tasks(yaml_text)
        assert len(tasks) == 2
        assert tasks[0].name == "task1"
        assert tasks[1].name == "task2"

    def test_parse_tasks_dict(self):
        """Parse YAML with tasks key."""
        yaml_text = """
tasks:
  - name: task1
    description: First task
    files: []
"""
        tasks = _parse_yaml_tasks(yaml_text)
        assert len(tasks) == 1
        assert tasks[0].name == "task1"

    def test_default_name_from_index(self):
        """Task name defaults to task-N."""
        yaml_text = """
- description: Task without name
  files: []
"""
        tasks = _parse_yaml_tasks(yaml_text)
        assert tasks[0].name == "task-1"

    def test_spec_falls_back_to_description(self):
        """Spec falls back to description."""
        yaml_text = """
- name: task1
  description: My description
  files: []
"""
        tasks = _parse_yaml_tasks(yaml_text)
        assert tasks[0].spec == "My description"

    def test_invalid_entry_raises(self):
        """Non-dict entry raises ValueError."""
        yaml_text = """
- "just a string"
"""
        with pytest.raises(ValueError, match="must be mappings"):
            _parse_yaml_tasks(yaml_text)


class TestEstimateComplexity:
    """Tests for estimate_complexity function."""

    def test_simple_spec(self):
        """Simple spec with no code blocks or files."""
        spec = "Create a simple function"
        score = estimate_complexity(spec)
        assert score.level == "simple"
        assert score.code_blocks == 0

    def test_spec_with_code_block(self):
        """Spec with code block counts correctly."""
        spec = """
Create a function:

```python
def hello():
    print("hello")
```
"""
        score = estimate_complexity(spec)
        assert score.code_blocks == 1
        assert score.estimated_lines == 2

    def test_spec_with_multiple_code_blocks(self):
        """Spec with multiple code blocks."""
        spec = """
```python
def foo():
    pass
```

```python
def bar():
    pass
```
"""
        score = estimate_complexity(spec)
        assert score.code_blocks == 2

    def test_spec_with_verification_section(self):
        """Spec with verification section."""
        spec = """
## Verification

```bash
pytest tests/
```
"""
        score = estimate_complexity(spec)
        assert score.verification_commands == 1

    def test_files_referenced(self):
        """Files referenced are counted."""
        spec = """
Modify src/main.py and tests/test_main.py
"""
        score = estimate_complexity(spec)
        assert score.files_referenced >= 1

    def test_complex_level(self):
        """Complex spec gets complex level."""
        spec = """
Create these files:
- src/main.py
- src/utils.py
- src/config.py
- tests/test_main.py

```python
# lots of code here
def main():
    pass
```

## Verification

```bash
pytest
```

```bash
mypy src/
```
"""
        score = estimate_complexity(spec)
        # Score > 6 should be complex
        assert score.level in ("medium", "complex")


class TestScoreSpecQuality:
    """Tests for score_spec_quality function."""

    def test_empty_spec_returns_zeros(self):
        """Empty spec returns all zeros."""
        result = score_spec_quality("")
        assert result == {
            "clarity": 0,
            "scope": 0,
            "constraints": 0,
            "verification": 0,
            "tool_budget": 0,
            "total": 0,
        }

    def test_whitespace_spec_returns_zeros(self):
        """Whitespace-only spec returns zeros."""
        result = score_spec_quality("   \n\t  ")
        assert result["total"] == 0

    def test_output_path_improves_clarity(self):
        """Output path improves clarity score."""
        spec = "Write the result to output.txt"
        result = score_spec_quality(spec)
        assert result["clarity"] > 0

    def test_verification_section_improves_score(self):
        """Verification section improves verification score."""
        spec = """
## Verification

Run pytest
"""
        result = score_spec_quality(spec)
        assert result["verification"] >= 5

    def test_pytest_mentioned(self):
        """Pytest mention improves verification score."""
        spec = "Run pytest to verify"
        result = score_spec_quality(spec)
        assert result["verification"] >= 3

    def test_constraints_detected(self):
        """Do not constraints detected."""
        spec = "Do not modify existing tests. Do not add new dependencies."
        result = score_spec_quality(spec)
        assert result["constraints"] >= 5

    def test_tool_budget_mentioned(self):
        """Tool budget mentioned improves score."""
        spec = "Max 10 tool calls allowed"
        result = score_spec_quality(spec)
        assert result["tool_budget"] > 0

    def test_multiple_deliverables_penalizes_scope(self):
        """Multiple deliverables penalizes scope."""
        spec = """
Create these files:
- src/main.py
- src/utils.py
- src/config.py
- src/handlers.py
"""
        result = score_spec_quality(spec)
        # Multiple output files should reduce scope score
        assert result["scope"] < 10


class TestLintPlan:
    """Tests for lint_plan function."""

    def test_empty_plan_warnings(self):
        """Empty plan returns multiple warnings."""
        warnings = lint_plan("")
        assert len(warnings) == 3
        assert any("output path" in w.lower() for w in warnings)
        assert any("constraints" in w.lower() for w in warnings)
        assert any("verification" in w.lower() for w in warnings)

    def test_good_plan_no_warnings(self):
        """Good plan has no warnings."""
        spec = """
## Output

Write to src/main.py

## Constraints

Do not modify existing tests.

## Verification

```bash
pytest
```
"""
        warnings = lint_plan(spec)
        assert len(warnings) == 0

    def test_tmp_path_warning(self):
        """References to /tmp/ produce warning."""
        spec = "Save the file to /tmp/output.txt"
        warnings = lint_plan(spec)
        assert any("/tmp/" in w for w in warnings)

    def test_todo_warning(self):
        """TODO markers produce warning."""
        spec = "Create the TODO implementation"
        warnings = lint_plan(spec)
        assert any("TODO" in w for w in warnings)

    def test_fixme_warning(self):
        """FIXME markers produce warning."""
        spec = "Create the FIXME implementation"
        warnings = lint_plan(spec)
        assert any("FIXME" in w for w in warnings)

    def test_missing_output_path_warning(self):
        """Missing output path produces warning."""
        spec = """
## Constraints
Do not break things.

## Verification
pytest
"""
        warnings = lint_plan(spec)
        assert any("output path" in w.lower() for w in warnings)


class TestDecomposePlan:
    """Tests for decompose_plan function."""

    def test_yaml_plan_parsed(self, tmp_path):
        """YAML plan file is parsed correctly."""
        yaml_content = """
- name: task1
  description: First task
  files: [file1.py]
  spec: Do something
"""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text(yaml_content)
        
        tasks = decompose_plan(plan_file)
        assert len(tasks) == 1
        assert tasks[0].name == "task1"

    def test_yml_extension_parsed(self, tmp_path):
        """YML extension is also parsed as YAML."""
        yaml_content = """
- name: task1
  description: Task
  files: []
"""
        plan_file = tmp_path / "plan.yml"
        plan_file.write_text(yaml_content)
        
        tasks = decompose_plan(plan_file)
        assert len(tasks) == 1

    def test_markdown_plan_creates_single_task(self, tmp_path):
        """Non-YAML plan creates single task."""
        md_content = """
# My Plan

Create a function that does X.
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(md_content)
        
        tasks = decompose_plan(plan_file)
        assert len(tasks) == 1
        assert tasks[0].name == "plan"

    def test_temp_file_created(self, tmp_path):
        """Temp file is created for task spec."""
        yaml_content = """
- name: task1
  description: Task
  spec: Do something
  files: []
"""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text(yaml_content)
        
        tasks = decompose_plan(plan_file)
        assert tasks[0].temp_file is not None
        assert Path(tasks[0].temp_file).exists()
        assert Path(tasks[0].temp_file).read_text() == "Do something"

    def test_smart_mode_calls_gemini(self, tmp_path):
        """Smart mode calls Gemini decomposition."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Create a function")
        
        mock_output = """
```yaml
- name: generated-task
  description: Generated
  files: []
```
"""
        
        with patch("metabolon.sortase.decompose._run_gemini_decomposition", return_value=mock_output):
            tasks = decompose_plan(plan_file, smart=True)
        
        assert len(tasks) == 1
        assert tasks[0].name == "generated-task"
