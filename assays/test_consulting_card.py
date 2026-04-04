from __future__ import annotations

"""Tests for effectors/consulting-card — consulting card skeleton generator.

Effectors are scripts, not importable modules. Tests invoke via subprocess.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

EFFECTOR = Path(__file__).resolve().parents[1] / "effectors" / "consulting-card"
CARDS_DIR = Path.home() / "epigenome/chromatin/euchromatin/consulting/cards"


def _run(*args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    """Run consulting-card with given args and optional stdin."""
    return subprocess.run(
        [sys.executable, str(EFFECTOR), *args],
        capture_output=True,
        text=True,
        timeout=30,
        input=stdin,
    )


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ── Generation tests ──────────────────────────────────────────────────────


class TestGenerate:
    def test_generates_card_with_all_sections(self, tmp_path: Path):
        out = tmp_path / "card.md"
        r = _run("--topic", "AI incident response", "--output", str(out))
        assert r.returncode == 0, r.stderr
        assert out.exists()
        content = out.read_text()
        for section in (
            "## Problem",
            "## Why It Matters",
            "## Approach",
            "## Considerations",
            "## Capco Angle",
        ):
            assert section in content, f"Missing section: {section}"

    def test_card_contains_todo_placeholders(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "Model risk", "--output", str(out))
        content = out.read_text()
        todos = [line for line in content.splitlines() if "[TODO:" in line]
        assert len(todos) >= 5, f"Expected >= 5 TODOs, got {len(todos)}"

    def test_card_title_matches_topic(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "AI bias testing", "--output", str(out))
        content = out.read_text()
        assert content.startswith("# AI bias testing")

    def test_card_has_slug_comment(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "DORA compliance", "--output", str(out))
        content = out.read_text()
        assert "slug: dora-compliance" in content
        assert "generated:" in content

    def test_approach_numbered_steps(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "LLM deployment risks", "--output", str(out))
        content = out.read_text()
        assert "1." in content
        assert "5." in content

    def test_why_it_matters_has_bullets(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "Vendor due diligence", "--output", str(out))
        content = out.read_text()
        # Should have at least 3 bullet points in why-it-matters
        lines = content.splitlines()
        in_section = False
        bullet_count = 0
        for line in lines:
            if "## Why It Matters" in line:
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("- "):
                bullet_count += 1
        assert bullet_count == 3, f"Expected 3 bullets, got {bullet_count}"

    def test_creates_parent_directories(self, tmp_path: Path):
        out = tmp_path / "nested" / "deep" / "card.md"
        r = _run("--topic", "Test topic", "--output", str(out))
        assert r.returncode == 0, r.stderr
        assert out.exists()

    def test_stdout_confirms_write(self, tmp_path: Path):
        out = tmp_path / "card.md"
        r = _run("--topic", "Test", "--output", str(out))
        assert f"Card written to {out}" in r.stdout


# ── YAML template from stdin ──────────────────────────────────────────────


class TestStdinTemplate:
    def test_yaml_template_overrides_default(self, tmp_path: Path):
        out = tmp_path / "card.md"
        yaml_input = textwrap.dedent("""\
            sections:
              problem: "Custom problem prompt."
              why-it-matters:
                - "Custom bullet 1."
              approach:
                - "Custom step A."
              considerations: "Custom consideration."
              capco-angle: "Custom Capco angle."
        """)
        r = _run("--topic", "Custom topic", "--output", str(out), stdin=yaml_input)
        assert r.returncode == 0, r.stderr
        content = out.read_text()
        assert "Custom problem prompt." in content
        assert "Custom bullet 1." in content
        assert "Custom step A." in content
        assert "Custom consideration." in content
        assert "Custom Capco angle." in content

    def test_partial_yaml_keeps_defaults(self, tmp_path: Path):
        out = tmp_path / "card.md"
        yaml_input = "sections:\n  problem: 'Only this changed.'\n"
        r = _run("--topic", "Partial", "--output", str(out), stdin=yaml_input)
        assert r.returncode == 0, r.stderr
        content = out.read_text()
        assert "Only this changed." in content
        # Default approach steps should still appear
        assert "Step 1:" in content

    def test_invalid_yaml_falls_back_to_default(self, tmp_path: Path):
        out = tmp_path / "card.md"
        r = _run("--topic", "Bad YAML", "--output", str(out), stdin="{{not yaml}}")
        assert r.returncode == 0, r.stderr
        content = out.read_text()
        # Should still have default structure
        assert "## Problem" in content
        assert "## Capco Angle" in content


# ── Slug generation ───────────────────────────────────────────────────────


class TestSlug:
    def test_slug_in_output(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "AI Incident Response Playbook", "--output", str(out))
        content = out.read_text()
        assert "slug: ai-incident-response-playbook" in content

    def test_slug_special_characters(self, tmp_path: Path):
        out = tmp_path / "card.md"
        _run("--topic", "DORA & AI: What's Next?", "--output", str(out))
        content = out.read_text()
        assert "slug: dora-ai-what-s-next" in content


# ── List / search ─────────────────────────────────────────────────────────


class TestList:
    @pytest.mark.skipif(not CARDS_DIR.exists(), reason="Cards directory not available")
    def test_list_all_cards(self):
        r = _run("--list")
        assert r.returncode == 0, r.stderr
        assert "card(s) found" in r.stdout

    @pytest.mark.skipif(not CARDS_DIR.exists(), reason="Cards directory not available")
    def test_list_search_keyword(self):
        r = _run("--list", "incident")
        assert r.returncode == 0, r.stderr
        # Should find at least ai-incident-response.md
        if "No cards found" not in r.stdout:
            assert "incident" in r.stdout.lower()

    @pytest.mark.skipif(not CARDS_DIR.exists(), reason="Cards directory not available")
    def test_list_no_match_returns_zero(self):
        r = _run("--list", "xyzzy_no_such_card_topic_12345")
        assert r.returncode == 0
        assert "No cards found" in r.stdout


# ── CLI edge cases ────────────────────────────────────────────────────────


class TestCLI:
    def test_no_args_shows_help(self):
        r = _run()
        assert r.returncode == 1
        assert "consulting-card" in r.stdout or "usage" in r.stdout.lower()

    def test_subcommand_generate(self, tmp_path: Path):
        out = tmp_path / "card.md"
        r = _run("generate", "--topic", "Test via subcommand", "--output", str(out))
        assert r.returncode == 0, r.stderr
        assert out.exists()
        assert "# Test via subcommand" in out.read_text()

    def test_subcommand_list(self):
        if not CARDS_DIR.exists():
            pytest.skip("Cards directory not available")
        r = _run("list")
        assert r.returncode == 0, r.stderr
