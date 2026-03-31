from __future__ import annotations

"""Tests for skill-lint — SKILL.md validator for membrane/receptors/."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest


# ── Load effector via exec (never import) ────────────────────────────


EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "skill-lint"


def _load_skill_lint():
    """Load the skill-lint module by exec-ing its Python body."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "skill_lint", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_skill_lint()
find_receptor_dirs = _mod["find_receptor_dirs"]
parse_frontmatter = _mod["parse_frontmatter"]
validate_skill_md = _mod["validate_skill_md"]
lint_receptors = _mod["lint_receptors"]
main = _mod["main"]
RECEPTORS_DIR = _mod["RECEPTORS_DIR"]


@contextmanager
def _patch_receptors_dir(new_dir: Path):
    """Context manager to temporarily swap RECEPTORS_DIR in the exec'd namespace."""
    original = _mod["RECEPTORS_DIR"]
    _mod["RECEPTORS_DIR"] = new_dir
    try:
        yield
    finally:
        _mod["RECEPTORS_DIR"] = original


# ── parse_frontmatter tests ──────────────────────────────────────────


class TestParseFrontmatter:
    """Tests for parse_frontmatter: valid YAML, missing markers, bad YAML."""

    def test_valid_frontmatter(self):
        """parse_frontmatter returns dict for valid YAML between --- markers."""
        content = "---\nname: foo\ndescription: bar\n---\nBody here\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm == {"name": "foo", "description": "bar"}

    def test_missing_opening_marker(self):
        """parse_frontmatter returns error when --- markers are absent."""
        content = "name: foo\ndescription: bar\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert "no YAML frontmatter" in err

    def test_missing_closing_marker(self):
        """parse_frontmatter returns error when closing --- is missing."""
        content = "---\nname: foo\ndescription: bar\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert "no YAML frontmatter" in err

    def test_invalid_yaml(self):
        """parse_frontmatter returns error for malformed YAML."""
        content = "---\n: invalid: yaml: [:\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert "YAML parse error" in err

    def test_frontmatter_is_list_not_dict(self):
        """parse_frontmatter returns error when YAML parses to a list."""
        content = "---\n- item1\n- item2\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert "list" in err

    def test_frontmatter_is_string_not_dict(self):
        """parse_frontmatter returns error when YAML parses to a plain string."""
        content = "---\njust a string\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert "str" in err

    def test_empty_frontmatter_blocks(self):
        """parse_frontmatter returns error when frontmatter block is empty (---\\n\\n---)."""
        # Regex requires content between markers; bare ---\\n--- has no match
        content = "---\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert fm is None
        assert err is not None

    def test_extra_whitespace_in_markers(self):
        """parse_frontmatter tolerates trailing spaces after ---."""
        content = "---  \nname: foo\ndescription: bar\n---  \nBody\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm["name"] == "foo"

    def test_multiple_fields(self):
        """parse_frontmatter parses all YAML fields correctly."""
        content = "---\nname: test\ndescription: desc\nrequires: browser\nuser_invocable: true\n---\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm["name"] == "test"
        assert fm["user_invocable"] is True

    def test_multiline_description(self):
        """parse_frontmatter handles multiline string values."""
        content = "---\nname: test\ndescription: |\n  Line one\n  Line two\n---\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert "Line one" in fm["description"]


# ── validate_skill_md tests ──────────────────────────────────────────


class TestValidateSkillMd:
    """Tests for validate_skill_md: missing file, valid, missing fields."""

    def test_missing_file(self, tmp_path):
        """validate_skill_md returns MISSING for non-existent file."""
        status, issues = validate_skill_md(tmp_path / "nope.md")
        assert status == "MISSING"
        assert "not found" in issues[0]

    def test_valid_skill_md(self, tmp_path):
        """validate_skill_md returns PASS for file with name and description."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"
        assert issues == []

    def test_missing_name_field(self, tmp_path):
        """validate_skill_md returns FAIL when name is absent."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("name" in i for i in issues)

    def test_missing_description_field(self, tmp_path):
        """validate_skill_md returns FAIL when description is absent."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("description" in i for i in issues)

    def test_empty_name(self, tmp_path):
        """validate_skill_md returns FAIL when name is empty string."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: ''\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_empty_description(self, tmp_path):
        """validate_skill_md returns FAIL when description is whitespace."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: '   '\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_name_is_number(self, tmp_path):
        """validate_skill_md returns FAIL when name is not a string."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: 42\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_description_is_number(self, tmp_path):
        """validate_skill_md returns FAIL when description is not a string."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: 42\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_no_frontmatter(self, tmp_path):
        """validate_skill_md returns FAIL for file without frontmatter."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("Just plain text\nNo frontmatter\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("frontmatter" in i for i in issues)

    def test_both_fields_missing(self, tmp_path):
        """validate_skill_md reports both missing fields."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nother: value\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert len(issues) == 2
        field_names = [i.split(":")[-1].strip() for i in issues]
        assert "name" in field_names
        assert "description" in field_names


# ── find_receptor_dirs tests ─────────────────────────────────────────


class TestFindReceptorDirs:
    """Tests for find_receptor_dirs: real dir, mocked missing dir."""

    def test_returns_list(self):
        """find_receptor_dirs returns a list."""
        result = find_receptor_dirs()
        assert isinstance(result, list)

    def test_real_receptors_dir_populated(self):
        """find_receptor_dirs finds real receptor directories."""
        result = find_receptor_dirs()
        if RECEPTORS_DIR.exists():
            assert len(result) > 0
            # All entries should be directories
            for d in result:
                assert d.is_dir()

    def test_nonexistent_receptors_dir(self, tmp_path):
        """find_receptor_dirs returns empty list when dir is missing."""
        with _patch_receptors_dir(tmp_path / "nope"):
            result = find_receptor_dirs()
        assert result == []

    def test_hidden_dirs_excluded(self, tmp_path):
        """find_receptor_dirs excludes hidden directories."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        (receptors / ".hidden").mkdir()
        (receptors / "visible").mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert "visible" in names
        assert ".hidden" not in names

    def test_sorted_output(self, tmp_path):
        """find_receptor_dirs returns sorted results."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for name in ("charlie", "alpha", "bravo"):
            (receptors / name).mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert names == sorted(names)

    def test_files_excluded(self, tmp_path):
        """find_receptor_dirs excludes plain files."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        (receptors / "adir").mkdir()
        (receptors / "afile.txt").write_text("hello")
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert "adir" in names
        assert "afile.txt" not in names


# ── lint_receptors tests ─────────────────────────────────────────────


class TestLintReceptors:
    """Tests for lint_receptors: mocked receptor dirs."""

    def _make_receptors(self, tmp_path, specs: dict[str, str | None]):
        """Create receptor dirs with optional SKILL.md content.

        specs: {dir_name: skill_md_content or None for missing}
        """
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for name, content in specs.items():
            d = receptors / name
            d.mkdir()
            if content is not None:
                (d / "SKILL.md").write_text(content)
        return receptors

    def test_all_valid(self, tmp_path):
        """lint_receptors returns all PASS for valid SKILL.md files."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        receptors = self._make_receptors(tmp_path, {
            "alpha": valid,
            "bravo": valid,
        })
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert len(results) == 2
        assert all(r["status"] == "PASS" for r in results)

    def test_missing_skill_md(self, tmp_path):
        """lint_receptors returns MISSING for dirs without SKILL.md."""
        receptors = self._make_receptors(tmp_path, {"alpha": None})
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert len(results) == 1
        assert results[0]["status"] == "MISSING"

    def test_mixed_results(self, tmp_path):
        """lint_receptors handles mix of PASS, FAIL, MISSING."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        bad = "---\nname: foo\n---\nBody\n"  # missing description
        receptors = self._make_receptors(tmp_path, {
            "good": valid,
            "bad": bad,
            "empty": None,
        })
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        by_name = {r["receptor"]: r for r in results}
        assert by_name["good"]["status"] == "PASS"
        assert by_name["bad"]["status"] == "FAIL"
        assert by_name["empty"]["status"] == "MISSING"

    def test_result_structure(self, tmp_path):
        """lint_receptors results have expected keys."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        receptors = self._make_receptors(tmp_path, {"alpha": valid})
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert len(results) == 1
        r = results[0]
        assert "receptor" in r
        assert "path" in r
        assert "status" in r
        assert "issues" in r
        assert isinstance(r["issues"], list)

    def test_empty_receptors_dir(self, tmp_path):
        """lint_receptors returns empty list when no receptor dirs exist."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert results == []


# ── main() tests ─────────────────────────────────────────────────────


class TestMain:
    """Tests for main: text output, JSON output, exit codes."""

    def _make_valid_receptors(self, tmp_path):
        """Create a receptors dir with one valid SKILL.md."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "test-receptor"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\ndescription: a test\n---\nBody\n")
        return receptors

    def test_text_output(self, tmp_path, capsys):
        """main prints text table by default."""
        receptors = self._make_valid_receptors(tmp_path)
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "test-receptor" in out
        assert "PASS" in out

    def test_json_output(self, tmp_path, capsys):
        """main --json outputs valid JSON."""
        receptors = self._make_valid_receptors(tmp_path)
        with _patch_receptors_dir(receptors):
            rc = main(["--json"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert data[0]["receptor"] == "test-receptor"
        assert data[0]["status"] == "PASS"

    def test_exit_1_on_failure(self, tmp_path):
        """main returns 1 when any receptor fails validation."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "bad-receptor"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nother: value\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1

    def test_exit_1_no_receptors(self, tmp_path, capsys):
        """main returns 1 when no receptor directories found."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1

    def test_text_output_shows_issues(self, tmp_path, capsys):
        """main text output includes issue descriptions for failures."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "broken"
        d.mkdir()
        (d / "SKILL.md").write_text("No frontmatter here\n")
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "frontmatter" in out

    def test_json_failure_structure(self, tmp_path, capsys):
        """main --json includes issues list for failures."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "broken"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main(["--json"])
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["status"] == "FAIL"
        assert len(data[0]["issues"]) > 0


# ── Integration: subprocess run ───────────────────────────────────────


class TestSubprocessRun:
    """Test the effector as a subprocess (integration)."""

    def test_script_runs(self):
        """skill-lint exits with 0 or 1 (pass or fail) but not crash."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode in (0, 1)

    def test_json_flag_runs(self):
        """skill-lint --json produces valid JSON output."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode in (0, 1)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert isinstance(data, list)


# ── Edge cases ───────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases: empty file, unicode, binary, YAML comments."""

    def test_empty_skill_md(self, tmp_path):
        """validate_skill_md returns FAIL for empty SKILL.md."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"

    def test_unicode_content(self, tmp_path):
        """validate_skill_md handles unicode in SKILL.md."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: 日本語テスト\ndescription: 説明文\n---\n本文\n", encoding="utf-8")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"

    def test_yaml_comments_in_frontmatter(self, tmp_path):
        """validate_skill_md ignores YAML comments."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\n# a comment\nname: foo\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"

    def test_extra_yaml_fields_ok(self, tmp_path):
        """validate_skill_md passes files with extra YAML fields."""
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: foo\ndescription: bar\nrequires: browser\n"
            "user_invocable: true\ntriggers:\n  - foo\n  - bar\n---\nBody\n"
        )
        status, issues = validate_skill_md(skill)
        assert status == "PASS"
        assert issues == []

    def test_frontmatter_no_body(self, tmp_path):
        """validate_skill_md passes when frontmatter has no body after ---."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: bar\n---\n")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"

    def test_name_is_boolean(self, tmp_path):
        """validate_skill_md returns FAIL when name is a boolean."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: true\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_description_is_boolean(self, tmp_path):
        """validate_skill_md returns FAIL when description is a boolean."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: false\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_yaml_null_value(self, tmp_path):
        """validate_skill_md returns FAIL when name is null."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: null\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_whitespace_only_name(self, tmp_path):
        """validate_skill_md returns FAIL when name is whitespace only."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: '   '\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_whitespace_only_description(self, tmp_path):
        """validate_skill_md returns FAIL when description is whitespace only."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: '  '\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)

    def test_nested_yaml_values(self, tmp_path):
        """validate_skill_md passes with nested YAML structures as extra fields."""
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: foo\ndescription: bar\ntriggers:\n  - alpha\n"
            "  - beta\nconfig:\n  key: value\n---\nBody\n"
        )
        status, issues = validate_skill_md(skill)
        assert status == "PASS"
        assert issues == []


class TestFindReceptorDirsExtra:
    """Additional edge cases for find_receptor_dirs."""

    def test_symlink_to_dir_included(self, tmp_path):
        """find_receptor_dirs includes symlinked directories."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        target = tmp_path / "real_dir"
        target.mkdir()
        (receptors / "linked").symlink_to(target)
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert "linked" in names

    def test_many_dirs(self, tmp_path):
        """find_receptor_dirs handles many directories correctly."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for i in range(50):
            (receptors / f"receptor-{i:03d}").mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        assert len(result) == 50


class TestLintReceptorsExtra:
    """Additional lint_receptors tests."""

    def test_path_is_string_in_result(self, tmp_path):
        """lint_receptors returns path as a string, not Path object."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "alpha"
        d.mkdir()
        (d / "SKILL.md").write_text(valid)
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert isinstance(results[0]["path"], str)
        assert "SKILL.md" in results[0]["path"]

    def test_multiple_failures(self, tmp_path):
        """lint_receptors handles multiple failing receptors."""
        bad = "---\nother: value\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for name in ("bad1", "bad2", "bad3"):
            d = receptors / name
            d.mkdir()
            (d / "SKILL.md").write_text(bad)
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert len(results) == 3
        assert all(r["status"] == "FAIL" for r in results)


class TestMainExtra:
    """Additional main() edge cases."""

    def test_stderr_no_receptors(self, tmp_path, capsys):
        """main prints message to stderr when no receptor directories found."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "No receptor directories found" in err

    def test_text_output_format(self, tmp_path, capsys):
        """main text output uses | separator between fields."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "my-receptor"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\ndescription: a test\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        parts = out.strip().split(" | ")
        assert len(parts) == 3
        assert parts[0] == "my-receptor"
        assert parts[1] == "PASS"

    def test_text_output_em_dash_for_pass(self, tmp_path, capsys):
        """main text output shows em dash for passing receptors with no issues."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "good"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\ndescription: a test\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "—" in out  # em dash for no-issues

    def test_json_multiple_receptors(self, tmp_path, capsys):
        """main --json lists all receptors in output."""
        valid = "---\nname: test\ndescription: desc\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for name in ("alpha", "bravo", "charlie"):
            d = receptors / name
            d.mkdir()
            (d / "SKILL.md").write_text(valid)
        with _patch_receptors_dir(receptors):
            rc = main(["--json"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        names = {r["receptor"] for r in data}
        assert names == {"alpha", "bravo", "charlie"}

    def test_unknown_flags_ignored(self, tmp_path, capsys):
        """main ignores unknown flags (no crash)."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "test-receptor"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\ndescription: a test\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main(["--unknown-flag"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "test-receptor" in out


# ── Additional edge cases ──────────────────────────────────────────────


class TestValidateSkillMdRobustness:
    """Robustness tests for validate_skill_md: binary, large, encoding edge cases."""

    def test_binary_file_content(self, tmp_path):
        """validate_skill_md returns FAIL for binary SKILL.md content."""
        skill = tmp_path / "SKILL.md"
        skill.write_bytes(b"\x00\x01\x02\xff\xfe\xfdbinary junk")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"

    def test_very_large_frontmatter(self, tmp_path):
        """validate_skill_md handles very large YAML frontmatter."""
        skill = tmp_path / "SKILL.md"
        long_desc = "x" * 50000
        skill.write_text(f"---\nname: test\ndescription: {long_desc}\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"
        assert issues == []

    def test_name_with_newlines(self, tmp_path):
        """validate_skill_md passes when name contains newlines (YAML folded scalar)."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: |\n  line1\n  line2\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "PASS"

    def test_description_with_special_chars(self, tmp_path):
        """validate_skill_md handles special characters in description."""
        skill = tmp_path / "SKILL.md"
        skill.write_text('---\nname: test\ndescription: "foo: bar & baz < qux > quux"\n---\nBody\n')
        status, issues = validate_skill_md(skill)
        assert status == "PASS"

    def test_missing_closing_marker_with_body(self, tmp_path):
        """validate_skill_md returns FAIL for frontmatter without closing ---."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: foo\ndescription: bar\nBody text continues\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("frontmatter" in i for i in issues)

    def test_frontmatter_only_dashes(self, tmp_path):
        """validate_skill_md returns FAIL when frontmatter is only dashes."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\n---\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"

    def test_single_dash_line(self, tmp_path):
        """validate_skill_md does not confuse single - with --- markers."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("-\nname: foo\ndescription: bar\n-\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"

    def test_yaml_float_name(self, tmp_path):
        """validate_skill_md returns FAIL when name parses as a float."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: 3.14\ndescription: bar\n---\nBody\n")
        status, issues = validate_skill_md(skill)
        assert status == "FAIL"
        assert any("non-empty" in i for i in issues)


class TestParseFrontmatterRobustness:
    """Additional parse_frontmatter edge cases."""

    def test_yaml_anchor_and_alias(self):
        """parse_frontmatter handles YAML anchors and aliases."""
        content = "---\ndefaults: &defaults\n  name: foo\ndescription: bar\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm["defaults"]["name"] == "foo"

    def test_yaml_with_dashes_in_value(self):
        """parse_frontmatter handles values containing dashes."""
        content = "---\nname: foo-bar-baz\ndescription: some --- value\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm["name"] == "foo-bar-baz"

    def test_yaml_null_key(self):
        """parse_frontmatter handles YAML with None/null key gracefully."""
        content = "---\n~: value\nname: foo\ndescription: bar\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        # Should still parse; null key is valid YAML
        assert err is None
        assert fm["name"] == "foo"

    def test_frontmatter_with_bom(self):
        """parse_frontmatter handles file with BOM (UTF-8 BOM before ---)."""
        content = "\ufeff---\nname: foo\ndescription: bar\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        # BOM prevents --- from being at line start; regex won't match
        assert fm is None
        assert err is not None

    def test_yaml_list_value(self):
        """parse_frontmatter handles YAML with list values."""
        content = "---\nname: foo\ndescription: bar\nrequires:\n  - alpha\n  - beta\n---\nBody\n"
        fm, err = parse_frontmatter(content)
        assert err is None
        assert fm["requires"] == ["alpha", "beta"]


class TestFindReceptorDirsRobustness:
    """Additional find_receptor_dirs edge cases."""

    def test_broken_symlink_excluded(self, tmp_path):
        """find_receptor_dirs excludes broken symlinks."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        target = tmp_path / "does_not_exist"
        (receptors / "broken").symlink_to(target)
        (receptors / "good").mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert "good" in names
        assert "broken" not in names

    def test_empty_receptors_dir(self, tmp_path):
        """find_receptor_dirs returns empty list for empty directory."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        assert result == []

    def test_nested_dirs_not_recurse(self, tmp_path):
        """find_receptor_dirs does not recurse into subdirectories."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        (receptors / "top").mkdir()
        (receptors / "top" / "nested").mkdir()
        with _patch_receptors_dir(receptors):
            result = find_receptor_dirs()
        names = [d.name for d in result]
        assert "top" in names
        assert "nested" not in names


class TestLintReceptorsRobustness:
    """Additional lint_receptors edge cases."""

    def test_missing_skill_md_path_correct(self, tmp_path):
        """lint_receptors returns correct path for missing SKILL.md."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "my-receptor"
        d.mkdir()
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert len(results) == 1
        assert "my-receptor" in results[0]["path"]
        assert "SKILL.md" in results[0]["path"]
        assert results[0]["status"] == "MISSING"

    def test_issues_list_always_present(self, tmp_path):
        """lint_receptors always returns issues list even for PASS."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "alpha"
        d.mkdir()
        (d / "SKILL.md").write_text(valid)
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        assert results[0]["issues"] == []

    def test_many_receptors_mixed(self, tmp_path):
        """lint_receptors handles many receptors with mixed statuses."""
        valid = "---\nname: foo\ndescription: bar\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        for i in range(20):
            d = receptors / f"r-{i:03d}"
            d.mkdir()
            if i % 3 == 0:
                pass  # no SKILL.md -> MISSING
            elif i % 3 == 1:
                (d / "SKILL.md").write_text(valid)  # PASS
            else:
                (d / "SKILL.md").write_text("---\nname: foo\n---\nBody\n")  # FAIL
        with _patch_receptors_dir(receptors):
            results = lint_receptors()
        statuses = {r["status"] for r in results}
        assert "MISSING" in statuses
        assert "PASS" in statuses
        assert "FAIL" in statuses
        assert len(results) == 20


class TestMainRobustness:
    """Additional main() edge cases."""

    def test_mixed_pass_fail_text_output(self, tmp_path, capsys):
        """main text output correctly shows both PASS and FAIL receptors."""
        valid = "---\nname: test\ndescription: desc\n---\nBody\n"
        bad = "---\nname: test\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d1 = receptors / "good"
        d1.mkdir()
        (d1 / "SKILL.md").write_text(valid)
        d2 = receptors / "bad"
        d2.mkdir()
        (d2 / "SKILL.md").write_text(bad)
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "good" in out
        assert "PASS" in out
        assert "bad" in out
        assert "FAIL" in out

    def test_json_mixed_pass_fail(self, tmp_path, capsys):
        """main --json returns correct structure for mix of pass/fail."""
        valid = "---\nname: test\ndescription: desc\n---\nBody\n"
        bad = "---\nname: test\n---\nBody\n"
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d1 = receptors / "good"
        d1.mkdir()
        (d1 / "SKILL.md").write_text(valid)
        d2 = receptors / "bad"
        d2.mkdir()
        (d2 / "SKILL.md").write_text(bad)
        with _patch_receptors_dir(receptors):
            rc = main(["--json"])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        by_name = {r["receptor"]: r for r in data}
        assert by_name["good"]["status"] == "PASS"
        assert by_name["bad"]["status"] == "FAIL"
        assert by_name["bad"]["issues"] != []

    def test_stderr_only_on_no_receptors(self, tmp_path, capsys):
        """main does not write to stdout when no receptors found (only stderr)."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "No receptor directories found" in captured.err

    def test_single_receptor_pass(self, tmp_path, capsys):
        """main returns 0 and prints one line for single passing receptor."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "solo"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: solo\ndescription: lone skill\n---\nBody\n")
        with _patch_receptors_dir(receptors):
            rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        lines = [l for l in out.strip().splitlines() if l.strip()]
        assert len(lines) == 1
        assert "solo" in lines[0]

    def test_json_missing_receptor_has_issues(self, tmp_path, capsys):
        """main --json for MISSING receptor includes 'SKILL.md not found' issue."""
        receptors = tmp_path / "receptors"
        receptors.mkdir()
        d = receptors / "missing"
        d.mkdir()
        with _patch_receptors_dir(receptors):
            rc = main(["--json"])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data[0]["status"] == "MISSING"
        assert any("not found" in i for i in data[0]["issues"])


class TestSubprocessRobustness:
    """Additional subprocess integration tests."""

    def test_json_output_on_failure(self):
        """skill-lint --json with real receptors produces valid JSON even on failures."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # May be 0 or 1 depending on real receptor state
        assert result.returncode in (0, 1)
        if result.returncode == 1 and result.stdout.strip():
            # If there's output on failure, it should be valid JSON
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0
            # Each entry has expected keys
            for entry in data:
                assert "receptor" in entry
                assert "status" in entry
                assert "issues" in entry

    def test_help_or_unknown_flag(self):
        """skill-lint does not crash with unexpected arguments."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR_PATH), "--nonexistent"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode in (0, 1)

    def test_stderr_on_no_receptors_from_subprocess(self):
        """skill-lint writes to stderr when run as subprocess with no receptors."""
        # We can't easily control RECEPTORS_DIR from subprocess, so just verify
        # stderr is empty or has expected message (real receptors likely exist)
        result = subprocess.run(
            [sys.executable, str(EFFECTOR_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Just verify it doesn't crash
        assert result.returncode in (0, 1)
