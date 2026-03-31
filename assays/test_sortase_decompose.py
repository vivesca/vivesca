from __future__ import annotations
"""Tests for sortase decompose."""

from pathlib import Path

import pytest
import yaml

from metabolon.sortase.decompose import (
    ComplexityScore,
    TaskSpec,
    _parse_yaml_tasks,
    _write_temp_specs,
    decompose_plan,
    estimate_complexity,
    score_spec_quality,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_MARKDOWN = """\
# Fix the login bug

The login page throws a 500 when the password contains special characters.
Fix the validation in auth.py.
"""

YAML_MULTI_TASK = """\
tasks:
  - name: add-user-model
    description: Create the User SQLAlchemy model
    spec: Create src/models/user.py with a User model having id, email, name columns.
    files:
      - src/models/user.py
    signal: boilerplate

  - name: add-user-routes
    description: Add CRUD routes for users
    spec: Create src/routes/users.py with GET /users, POST /users, GET /users/{id}.
    files:
      - src/routes/users.py
    signal: boilerplate
    prerequisite: add-user-model
"""

YAML_SINGLE_TASK = """\
tasks:
  - name: fix-typo
    description: Fix typo in README
    spec: Change "helo world" to "hello world" in README.md.
    files:
      - README.md
"""

YAML_WITH_SIGNAL = """\
tasks:
  - name: optimize-sort
    description: Optimize the sorting algorithm
    spec: Replace bubble sort with merge sort in src/sort.py.
    files:
      - src/sort.py
    signal: algorithmic
"""

YAML_TOP_LEVEL_LIST = """\
- name: top-level-task
  description: A task in a top-level list
  spec: Do something useful.
  files:
    - src/main.py
  signal: rust
"""

YAML_WITH_DEFAULTS = """\
tasks:
  - description: Task with minimal fields
    spec: Just a spec, no name or signal.
    files:
      - src/foo.py
"""


# ---------------------------------------------------------------------------
# Tests: TaskSpec dataclass
# ---------------------------------------------------------------------------

class TestTaskSpec:
    def test_fields(self):
        ts = TaskSpec(
            name="my-task",
            description="desc",
            spec="do stuff",
            files=["a.py", "b.py"],
            signal="boilerplate",
            prerequisite="other-task",
            temp_file="/tmp/sortase-task-1.txt",
        )
        assert ts.name == "my-task"
        assert ts.description == "desc"
        assert ts.spec == "do stuff"
        assert ts.files == ["a.py", "b.py"]
        assert ts.signal == "boilerplate"
        assert ts.prerequisite == "other-task"
        assert ts.temp_file == "/tmp/sortase-task-1.txt"

    def test_defaults(self):
        ts = TaskSpec(name="t", description="d", spec="s", files=[])
        assert ts.signal == "default"
        assert ts.prerequisite is None
        assert ts.temp_file is None

    def test_frozen(self):
        ts = TaskSpec(name="t", description="d", spec="s", files=[])
        with pytest.raises(AttributeError):
            ts.name = "changed"


# ---------------------------------------------------------------------------
# Tests: _parse_yaml_tasks
# ---------------------------------------------------------------------------

class TestParseYamlTasks:
    def test_dict_with_tasks_key(self):
        tasks = _parse_yaml_tasks(YAML_MULTI_TASK)
        assert len(tasks) == 2
        assert tasks[0].name == "add-user-model"
        assert tasks[1].name == "add-user-routes"

    def test_top_level_list(self):
        tasks = _parse_yaml_tasks(YAML_TOP_LEVEL_LIST)
        assert len(tasks) == 1
        assert tasks[0].name == "top-level-task"
        assert tasks[0].signal == "rust"

    def test_signal_field(self):
        tasks = _parse_yaml_tasks(YAML_WITH_SIGNAL)
        assert tasks[0].signal == "algorithmic"

    def test_prerequisite_field(self):
        tasks = _parse_yaml_tasks(YAML_MULTI_TASK)
        assert tasks[0].prerequisite is None
        assert tasks[1].prerequisite == "add-user-model"

    def test_defaults_when_missing_fields(self):
        tasks = _parse_yaml_tasks(YAML_WITH_DEFAULTS)
        assert len(tasks) == 1
        # name falls back to task-1
        assert tasks[0].name == "task-1"
        assert tasks[0].signal == "default"
        assert tasks[0].prerequisite is None

    def test_empty_tasks_list(self):
        tasks = _parse_yaml_tasks("tasks: []\n")
        assert tasks == []

    def test_none_payload(self):
        tasks = _parse_yaml_tasks("")
        assert tasks == []

    def test_invalid_entry_raises(self):
        with pytest.raises(ValueError, match="must be mappings"):
            _parse_yaml_tasks("tasks:\n  - not_a_dict\n")

    def test_description_falls_back_to_spec(self):
        raw = yaml.dump({"tasks": [{"name": "t", "spec": "the spec text", "files": []}]})
        tasks = _parse_yaml_tasks(raw)
        assert tasks[0].description == "the spec text"

    def test_spec_falls_back_to_description(self):
        raw = yaml.dump({"tasks": [{"name": "t", "description": "the desc text", "files": []}]})
        tasks = _parse_yaml_tasks(raw)
        assert tasks[0].spec == "the desc text"


# ---------------------------------------------------------------------------
# Tests: _write_temp_specs
# ---------------------------------------------------------------------------

class TestWriteTempSpecs:
    def test_writes_temp_files(self):
        tasks = [
            TaskSpec(name="a", description="d", spec="spec-a", files=[]),
            TaskSpec(name="b", description="d", spec="spec-b", files=[]),
        ]
        result = _write_temp_specs(tasks)
        assert len(result) == 2
        for t in result:
            assert t.temp_file is not None
            p = Path(t.temp_file)
            assert p.exists()
            assert p.read_text(encoding="utf-8") == t.spec
            # cleanup
            p.unlink()

    def test_preserves_all_fields(self):
        original = TaskSpec(
            name="x",
            description="d",
            spec="s",
            files=["f.py"],
            signal="rust",
            prerequisite="y",
        )
        result = _write_temp_specs([original])
        assert result[0].name == "x"
        assert result[0].description == "d"
        assert result[0].files == ["f.py"]
        assert result[0].signal == "rust"
        assert result[0].prerequisite == "y"
        # cleanup
        Path(result[0].temp_file).unlink()


# ---------------------------------------------------------------------------
# Tests: decompose_plan integration
# ---------------------------------------------------------------------------

class TestDecomposePlan:
    def test_markdown_single_task(self, tmp_path: Path):
        plan = tmp_path / "plan.md"
        plan.write_text(SIMPLE_MARKDOWN, encoding="utf-8")
        tasks = decompose_plan(plan)
        assert len(tasks) == 1
        assert tasks[0].name == "plan"
        assert tasks[0].spec == SIMPLE_MARKDOWN
        assert tasks[0].files == []
        assert tasks[0].signal == "default"
        assert tasks[0].temp_file is not None
        # cleanup
        Path(tasks[0].temp_file).unlink()

    def test_yaml_multi_task(self, tmp_path: Path):
        plan = tmp_path / "plan.yaml"
        plan.write_text(YAML_MULTI_TASK, encoding="utf-8")
        tasks = decompose_plan(plan)
        assert len(tasks) == 2
        assert tasks[0].name == "add-user-model"
        assert tasks[1].name == "add-user-routes"
        assert tasks[1].prerequisite == "add-user-model"
        assert all(t.temp_file is not None for t in tasks)
        # cleanup
        for t in tasks:
            Path(t.temp_file).unlink()

    def test_yaml_yml_extension(self, tmp_path: Path):
        plan = tmp_path / "plan.yml"
        plan.write_text(YAML_SINGLE_TASK, encoding="utf-8")
        tasks = decompose_plan(plan)
        assert len(tasks) == 1
        assert tasks[0].name == "fix-typo"
        Path(tasks[0].temp_file).unlink()

    def test_yaml_single_task(self, tmp_path: Path):
        plan = tmp_path / "single.yaml"
        plan.write_text(YAML_SINGLE_TASK, encoding="utf-8")
        tasks = decompose_plan(plan)
        assert len(tasks) == 1
        assert tasks[0].name == "fix-typo"
        assert tasks[0].files == ["README.md"]
        Path(tasks[0].temp_file).unlink()

    def test_markdown_uses_stem_as_name(self, tmp_path: Path):
        plan = tmp_path / "fix-auth-bug.md"
        plan.write_text("Fix the auth bug.", encoding="utf-8")
        tasks = decompose_plan(plan)
        assert tasks[0].name == "fix-auth-bug"
        Path(tasks[0].temp_file).unlink()

    def test_markdown_spaces_in_stem(self, tmp_path: Path):
        plan = tmp_path / "fix auth bug.md"
        plan.write_text("Fix the auth bug.", encoding="utf-8")
        tasks = decompose_plan(plan)
        assert tasks[0].name == "fix-auth-bug"
        Path(tasks[0].temp_file).unlink()

    def test_empty_yaml_plan(self, tmp_path: Path):
        plan = tmp_path / "empty.yaml"
        plan.write_text("tasks: []\n", encoding="utf-8")
        tasks = decompose_plan(plan)
        assert tasks == []

    def test_path_as_string(self, tmp_path: Path):
        plan = tmp_path / "plan.md"
        plan.write_text("Some task text", encoding="utf-8")
        tasks = decompose_plan(str(plan))
        assert len(tasks) == 1
        assert tasks[0].spec == "Some task text"
        Path(tasks[0].temp_file).unlink()


# ---------------------------------------------------------------------------
# Tests: estimate_complexity
# ---------------------------------------------------------------------------

SIMPLE_SPEC = "Fix the typo in README.md: change 'helo' to 'hello'."

MEDIUM_SPEC = """\
Modify two files to add logging:

## Verification
```bash
cd ~/germline && uv run pytest assays/test_foo.py -v
```

- src/main.py: add logger import and log call
- src/utils.py: add logger import and log call
"""

COMPLEX_SPEC = """\
Refactor the entire sortase pipeline:

### Files to modify:
- metabolon/sortase/decompose.py
- metabolon/sortase/router.py
- metabolon/sortase/executor.py
- metabolon/sortase/validator.py
- assays/test_sortase_decompose.py
- assays/test_sortase_router.py
- assays/test_sortase_executor.py
- assays/test_sortase_validator.py

### Steps
1. Add a ComplexityScore dataclass to decompose.py
2. Implement estimate_complexity() that counts files, code blocks, and verification commands
3. Update router.py to use complexity for timeout decisions
4. Update executor.py to retry based on complexity
5. Add comprehensive tests

## Verification
```bash
cd ~/germline && uv run pytest assays/test_sortase_decompose.py -v --tb=short
```
```bash
cd ~/germline && uv run pytest assays/test_sortase_router.py -v --tb=short
```
```bash
cd ~/germline && uv run pytest assays/test_sortase_executor.py -v --tb=short
```

Lines of code to change: approximately 150-200 lines across all files.
"""


class TestComplexityScore:
    def test_fields(self):
        cs = ComplexityScore(
            level="simple",
            files_referenced=1,
            code_blocks=0,
            verification_commands=0,
            estimated_lines=5,
        )
        assert cs.level == "simple"
        assert cs.files_referenced == 1
        assert cs.code_blocks == 0
        assert cs.verification_commands == 0
        assert cs.estimated_lines == 5

    def test_frozen(self):
        cs = ComplexityScore(
            level="simple", files_referenced=1, code_blocks=0,
            verification_commands=0, estimated_lines=5,
        )
        with pytest.raises(AttributeError):
            cs.level = "complex"


class TestEstimateComplexity:
    def test_simple_spec(self):
        result = estimate_complexity(SIMPLE_SPEC)
        assert result.level == "simple"
        assert result.files_referenced >= 1
        assert result.code_blocks == 0
        assert result.verification_commands == 0

    def test_medium_spec(self):
        result = estimate_complexity(MEDIUM_SPEC)
        assert result.level in ("simple", "medium")
        assert result.files_referenced >= 2
        assert result.verification_commands >= 1

    def test_complex_spec(self):
        result = estimate_complexity(COMPLEX_SPEC)
        assert result.level == "complex"
        assert result.files_referenced >= 8
        assert result.verification_commands >= 3

    def test_empty_spec(self):
        result = estimate_complexity("")
        assert result.level == "simple"
        assert result.files_referenced == 0
        assert result.code_blocks == 0
        assert result.verification_commands == 0
        assert result.estimated_lines == 0

    def test_code_blocks_counted(self):
        spec = "Do this:\n```python\nx = 1\n```\nAnd this:\n```\ny = 2\n```"
        result = estimate_complexity(spec)
        assert result.code_blocks == 2

    def test_verification_commands_counted(self):
        spec = "## Verification\n```bash\ncd ~/foo && pytest bar.py\n```"
        result = estimate_complexity(spec)
        assert result.verification_commands == 1

    def test_file_paths_in_markdown_list(self):
        spec = "- src/a.py: change X\n- src/b.py: change Y\n- src/c.py: change Z"
        result = estimate_complexity(spec)
        assert result.files_referenced >= 3

    def test_returns_complexity_score_type(self):
        result = estimate_complexity("some text")
        assert isinstance(result, ComplexityScore)

    def test_estimated_lines_from_code_blocks(self):
        spec = "```python\nline1\nline2\nline3\n```"
        result = estimate_complexity(spec)
        assert result.estimated_lines >= 3

    def test_level_is_one_of_three(self):
        for text in ["", "fix typo", COMPLEX_SPEC]:
            result = estimate_complexity(text)
            assert result.level in ("simple", "medium", "complex")


# ---------------------------------------------------------------------------
# Tests: score_spec_quality
# ---------------------------------------------------------------------------

MINIMAL_SPEC = "Fix the typo in README.md."

GOOD_SPEC = """\
# Add feature X

## Output
Write to src/feature_x.py.

## Scope
Single deliverable: create the feature module.

## Constraints
- Do NOT modify existing tests.
- Do NOT add new dependencies.

## Verification
```bash
cd ~/germline && uv run pytest assays/test_feature_x.py -v
```

## Tool budget
Max 15 tool calls.
"""

MULTI_DELIVERABLE_SPEC = """\
# Refactor and test

## Output
Write to src/refactor.py and tests/test_refactor.py.

## Verification
```bash
pytest tests/test_refactor.py
```
"""

NO_CONSTRAINTS_SPEC = """\
# Add logging

Write to src/logger.py.

## Verification
```bash
pytest tests/test_logger.py
```
"""

NO_VERIFICATION_SPEC = """\
# Add feature Y

Write to src/feature_y.py.

## Constraints
- Do NOT change src/other.py.
"""

NO_OUTPUT_PATH_SPEC = """\
# Fix something

## Constraints
- Do NOT break existing tests.

## Verification
```bash
pytest
```

## Tool budget
Max 10 tool calls.
"""

PERFECT_SPEC = """\
# Implement scoring

## Output path
Write the result to ~/germline/metabolon/sortase/scoring.py.

## Scope
Single deliverable: the scoring module.

## Constraints
- Do NOT import from private modules.
- Do NOT modify existing tests.

## Verification
```bash
cd ~/germline && uv run pytest assays/test_sortase_scoring.py -v --tb=short
```

## Tool budget
Max 20 tool calls.
"""

EMPTY_SPEC = ""


class TestScoreSpecQuality:
    def test_returns_dict_with_expected_keys(self):
        result = score_spec_quality("Do something.")
        for key in ("clarity", "scope", "constraints", "verification", "tool_budget", "total"):
            assert key in result, f"missing key: {key}"

    def test_minimal_spec_low_scores(self):
        result = score_spec_quality(MINIMAL_SPEC)
        assert result["clarity"] == 0
        assert result["scope"] == 0
        assert result["constraints"] == 0
        assert result["verification"] == 0
        assert result["tool_budget"] == 0
        assert result["total"] == 0

    def test_good_spec_high_scores(self):
        result = score_spec_quality(GOOD_SPEC)
        assert result["clarity"] >= 8
        assert result["scope"] >= 7
        assert result["constraints"] >= 7
        assert result["verification"] >= 7
        assert result["tool_budget"] >= 7
        assert result["total"] >= 35

    def test_perfect_spec_near_max(self):
        result = score_spec_quality(PERFECT_SPEC)
        assert result["clarity"] == 10
        assert result["scope"] == 10
        assert result["constraints"] == 10
        assert result["verification"] == 10
        assert result["tool_budget"] == 10
        assert result["total"] == 50

    def test_multi_deliverable_reduces_scope(self):
        result = score_spec_quality(MULTI_DELIVERABLE_SPEC)
        assert result["scope"] < 7

    def test_no_constraints_zero_constraints(self):
        result = score_spec_quality(NO_CONSTRAINTS_SPEC)
        assert result["constraints"] == 0

    def test_no_verification_zero_verification(self):
        result = score_spec_quality(NO_VERIFICATION_SPEC)
        assert result["verification"] == 0

    def test_no_output_path_reduces_clarity(self):
        result = score_spec_quality(NO_OUTPUT_PATH_SPEC)
        assert result["clarity"] <= 5

    def test_empty_spec_all_zeros(self):
        result = score_spec_quality(EMPTY_SPEC)
        assert result["total"] == 0

    def test_scores_are_integers(self):
        result = score_spec_quality(GOOD_SPEC)
        for key in ("clarity", "scope", "constraints", "verification", "tool_budget", "total"):
            assert isinstance(result[key], int), f"{key} should be int"

    def test_total_is_sum(self):
        result = score_spec_quality(GOOD_SPEC)
        assert result["total"] == (
            result["clarity"]
            + result["scope"]
            + result["constraints"]
            + result["verification"]
            + result["tool_budget"]
        )


# ---------------------------------------------------------------------------
# Tests: lint_plan
# ---------------------------------------------------------------------------

from metabolon.sortase.decompose import lint_plan

LINT_CLEAN_PLAN = """\
# Add feature X

## Output
Write to ~/germline/metabolon/sortase/feature_x.py.

## Constraints
- Do NOT modify existing tests.

## Verification
```bash
cd ~/germline && uv run pytest assays/test_feature_x.py -v
```
"""

LINT_ALL_ISSUES_PLAN = """\
# Do stuff

Write output to /tmp/scratch.py.

Some things still need work FIXME later.
Also there is a TODO about handling edge cases.
"""

LINT_NO_OUTPUT_PLAN = """\
# Fix the bug

## Constraints
- Do NOT break tests.

## Verification
```bash
pytest
```
"""

LINT_NO_CONSTRAINTS_PLAN = """\
# Add feature

Write to src/feature.py.

## Verification
```bash
pytest
```
"""

LINT_NO_VERIFICATION_PLAN = """\
# Add feature

Write to src/feature.py.

## Constraints
- Do NOT change other files.
"""

LINT_TMP_PLAN = """\
# Task

## Output
Write to /tmp/plan_output.md.

## Constraints
- Do NOT break anything.

## Verification
```bash
echo done
```
"""

LINT_TODO_FIXME_PLAN = """\
# Task

## Output
Write to ~/germline/loci/plans/output.md.

## Constraints
- Do NOT break anything.

TODO: add more details.
FIXME: this is wrong.
"""

LINT_EMPTY_PLAN = ""

LINT_MULTIPLE_TMP_PLAN = """\
# Task

Write to /tmp/a.py first, then copy to /tmp/b.py.

## Constraints
- Do NOT break anything.

## Verification
```bash
echo done
```
"""


class TestLintPlan:
    def test_clean_plan_no_warnings(self):
        warnings = lint_plan(LINT_CLEAN_PLAN)
        assert warnings == []

    def test_all_issues_detected(self):
        warnings = lint_plan(LINT_ALL_ISSUES_PLAN)
        # no output, no constraints, no verification, /tmp/, TODO, FIXME = 6
        assert len(warnings) == 6
        messages = " ".join(warnings)
        assert "/tmp/" in messages
        assert "FIXME" in messages
        assert "TODO" in messages
        assert "output path" in messages.lower()
        assert "constraints" in messages.lower()
        assert "verification" in messages.lower()

    def test_no_output_path_warning(self):
        warnings = lint_plan(LINT_NO_OUTPUT_PLAN)
        messages = " ".join(warnings)
        assert any("output path" in w.lower() for w in warnings)

    def test_no_constraints_warning(self):
        warnings = lint_plan(LINT_NO_CONSTRAINTS_PLAN)
        assert any("constraints" in w.lower() for w in warnings)

    def test_no_verification_warning(self):
        warnings = lint_plan(LINT_NO_VERIFICATION_PLAN)
        assert any("verification" in w.lower() for w in warnings)

    def test_tmp_path_warning(self):
        warnings = lint_plan(LINT_TMP_PLAN)
        assert any("/tmp/" in w for w in warnings)

    def test_todo_warning(self):
        warnings = lint_plan(LINT_TODO_FIXME_PLAN)
        assert any("TODO" in w for w in warnings)

    def test_fixme_warning(self):
        warnings = lint_plan(LINT_TODO_FIXME_PLAN)
        assert any("FIXME" in w for w in warnings)

    def test_empty_plan_warnings(self):
        warnings = lint_plan(LINT_EMPTY_PLAN)
        assert len(warnings) >= 3

    def test_returns_list_of_strings(self):
        warnings = lint_plan(LINT_ALL_ISSUES_PLAN)
        assert isinstance(warnings, list)
        for w in warnings:
            assert isinstance(w, str)

    def test_multiple_tmp_references_counted(self):
        warnings = lint_plan(LINT_MULTIPLE_TMP_PLAN)
        tmp_warnings = [w for w in warnings if "/tmp/" in w]
        assert len(tmp_warnings) >= 1
