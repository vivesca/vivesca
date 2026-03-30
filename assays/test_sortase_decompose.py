"""Tests for sortase decompose."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from metabolon.sortase.decompose import (
    TaskSpec,
    _parse_yaml_tasks,
    _write_temp_specs,
    decompose_plan,
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
