"""Tests for effectors/skill-search."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

EFFECTOR = Path(__file__).parent.parent / "effectors" / "skill-search"

# Load effector as module via exec
_NS: dict = {}
exec(open(EFFECTOR).read(), _NS)

search_skills = _NS["search_skills"]
format_results = _NS["format_results"]
parse_frontmatter = _NS["parse_frontmatter"]
get_body = _NS["get_body"]
main = _NS["main"]


# --- Helpers ---

def _make_skill(tmp_path: Path, name: str, description: str,
                triggers: list[str] | None = None, body: str = "") -> Path:
    """Create a minimal SKILL.md in a receptor subdirectory."""
    receptor_dir = tmp_path / name
    receptor_dir.mkdir(parents=True, exist_ok=True)
    skill = receptor_dir / "SKILL.md"
    trigger_yaml = "\n".join(f"  - {t}" for t in (triggers or []))
    skill.write_text(textwrap.dedent(f"""\
        ---
        name: {name}
        description: {description}
        triggers:
        {trigger_yaml}
        ---
        {body}
    """), encoding="utf-8")
    return skill


# --- Tests: parse_frontmatter ---

class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\nname: foo\ndescription: bar\n---\nBody text."
        fm = parse_frontmatter(content)
        assert fm["name"] == "foo"
        assert fm["description"] == "bar"

    def test_missing_frontmatter(self):
        content = "Just some text without frontmatter."
        fm = parse_frontmatter(content)
        assert fm == {}

    def test_triggers_list(self):
        content = "---\nname: x\ntriggers:\n  - alpha\n  - beta\n---\n"
        fm = parse_frontmatter(content)
        assert fm["triggers"] == ["alpha", "beta"]


# --- Tests: get_body ---

class TestGetBody:
    def test_extracts_body_after_frontmatter(self):
        content = "---\nname: x\n---\n# Heading\nSome body text."
        assert "# Heading" in get_body(content)
        assert "name" not in get_body(content)

    def test_no_frontmatter_returns_all(self):
        content = "Just body text."
        assert get_body(content) == "Just body text."


# --- Tests: search_skills ---

class TestSearchSkills:
    def test_search_by_name(self, tmp_path):
        _make_skill(tmp_path, "diagnosis", "Root cause analysis",
                    triggers=["debug", "broken"])
        with patch.object(_NS["Path"], "parent", new=lambda self: tmp_path):
            # We need to patch RECEPTORS_DIR instead
            pass

    def test_search_finds_name_match(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis",
                    triggers=["debug", "broken"])
        _make_skill(tmp_path, "histology", "Architecture review",
                    triggers=["structure"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["etiology"])
        assert len(results) == 1
        assert results[0]["name"] == "etiology"
        assert "name" in results[0]["matched_fields"]

    def test_search_finds_trigger_match(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis",
                    triggers=["debug", "broken"])
        _make_skill(tmp_path, "histology", "Architecture review",
                    triggers=["structure"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["debug"])
        assert len(results) == 1
        assert results[0]["name"] == "etiology"
        assert "triggers" in results[0]["matched_fields"]

    def test_search_finds_description_match(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis for bugs",
                    triggers=["debug"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["root-cause"])
        assert len(results) == 1
        assert "description" in results[0]["matched_fields"]

    def test_search_finds_body_match(self, tmp_path):
        _make_skill(tmp_path, "test-skill", "A skill",
                    body="This skill handles postmortem analysis.")
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["postmortem"])
        assert len(results) == 1
        assert "body" in results[0]["matched_fields"]

    def test_search_triggers_only_mode(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis",
                    triggers=["debug"],
                    body="Mention debug in the body text too.")
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["debug"], triggers_only=True)
        assert len(results) == 1
        # body should not be searched in triggers_only mode
        assert "body" not in results[0]["matched_fields"]
        assert "triggers" in results[0]["matched_fields"]

    def test_search_no_match(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis")
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["nonexistent"])
        assert results == []

    def test_ranking_name_beats_trigger(self, tmp_path):
        _make_skill(tmp_path, "debug", "Debugging tool", triggers=["trace"])
        _make_skill(tmp_path, "tracer", "Tracing tool", triggers=["debug"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["debug"])
        assert len(results) == 2
        assert results[0]["name"] == "debug"  # name match ranks higher

    def test_multi_keyword_search(self, tmp_path):
        _make_skill(tmp_path, "etiology", "Root-cause diagnosis",
                    triggers=["debug", "broken"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["debug", "broken"])
        assert len(results) == 1
        assert results[0]["score"] >= 4  # 2 trigger hits = 2*2 = 4

    def test_case_insensitive(self, tmp_path):
        _make_skill(tmp_path, "Etiology", "Diagnosis", triggers=["Debug"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            results = search_skills(["debug"])
        assert len(results) == 1


# --- Tests: format_results ---

class TestFormatResults:
    def test_empty_results(self):
        assert "No matching" in format_results([])

    def test_single_result(self):
        results = [{
            "name": "etiology",
            "description": "Root-cause diagnosis",
            "triggers": ["debug", "broken"],
            "path": "/some/path",
            "score": 3.0,
            "matched_fields": ["name"],
        }]
        output = format_results(results)
        assert "etiology" in output
        assert "Root-cause diagnosis" in output
        assert "debug" in output

    def test_multiple_results(self):
        results = [
            {
                "name": "a",
                "description": "desc a",
                "triggers": [],
                "path": "/a",
                "score": 3.0,
                "matched_fields": ["name"],
            },
            {
                "name": "b",
                "description": "desc b",
                "triggers": ["x"],
                "path": "/b",
                "score": 2.0,
                "matched_fields": ["triggers"],
            },
        ]
        output = format_results(results)
        assert "1. a" in output
        assert "2. b" in output


# --- Tests: main() ---

class TestMain:
    def test_help_exits_zero(self, capsys):
        assert main(["--help"]) == 0
        captured = capsys.readouterr()
        assert "Search SKILL.md" in captured.out

    def test_no_keywords_exits_one(self, capsys):
        assert main([]) == 1

    def test_json_output(self, tmp_path, capsys):
        _make_skill(tmp_path, "etiology", "Diagnosis", triggers=["debug"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            rc = main(["--json", "debug"])
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert data[0]["name"] == "etiology"

    def test_normal_output(self, tmp_path, capsys):
        _make_skill(tmp_path, "etiology", "Diagnosis", triggers=["debug"])
        with patch(_NS["__name__"] + ".RECEPTORS_DIR", tmp_path):
            rc = main(["debug"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "etiology" in captured.out
