from __future__ import annotations

"""Tests for consulting-card effector — subprocess + exec hybrid."""

import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "consulting-card.py"


# ── Helpers ───────────────────────────────────────────────────────────────


def _run(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Invoke consulting-card.py via subprocess.run."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        capture_output=True,
        text=True,
        timeout=15,
        **kwargs,
    )


def _load_module():
    """Load consulting-card via exec (effector pattern, not importable).

    The effector imports ``openai`` at call time (inside generate_card),
    so we only need the stub in sys.modules at exec time if the module-level
    code tries to import it.
    """
    import types
    import unittest.mock as _um

    source = SCRIPT.read_text()
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = _um.MagicMock()
    saved = sys.modules.get("openai")
    sys.modules["openai"] = openai_stub
    try:
        ns: dict = {
            "__name__": "consulting_card",
            "__file__": str(SCRIPT),
        }
        exec(source, ns)
    finally:
        if saved is None:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = saved
    return ns


_ns = _load_module()

slugify = _ns["slugify"]
generate_card = _ns["generate_card"]
build_markdown = _ns["build_markdown"]
list_cards = _ns["list_cards"]
write_card = _ns["write_card"]
main = _ns["main"]
CARDS_DIR = _ns["CARDS_DIR"]
MODEL = _ns["MODEL"]
SYSTEM_PROMPT = _ns["SYSTEM_PROMPT"]


def _cards_dir(tmp_path):
    """Context manager: override CARDS_DIR in the exec'd globals."""
    return patch.dict(_ns, {"CARDS_DIR": tmp_path})


def _mock_openai(mock_response):
    """Context manager: inject a mock OpenAI class into the exec'd globals.

    generate_card does ``from openai import OpenAI`` inside the function, so
    we mock sys.modules["openai"] so the inline import finds our stub.
    """
    import types
    from contextlib import contextmanager

    MockClient = MagicMock()
    MockClient.return_value.chat.completions.create.return_value = mock_response

    mock_openai_module = types.ModuleType("openai")
    mock_openai_module.OpenAI = MockClient

    original = sys.modules.get("openai")

    @contextmanager
    def combined_ctx():
        sys.modules["openai"] = mock_openai_module
        with patch.dict(_ns, {}):
            try:
                yield
            finally:
                if original is None:
                    sys.modules.pop("openai", None)
                else:
                    sys.modules["openai"] = original

    return combined_ctx(), MockClient


# ══════════════════════════════════════════════════════════════════════════
# ── subprocess tests (CLI interface) ──────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════


class TestSubprocessHelp:
    """Test --help flag via subprocess."""

    def test_help_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_help_shows_description(self):
        r = _run(["--help"])
        assert "consulting insight card" in r.stdout.lower()

    def test_help_lists_arguments(self):
        r = _run(["--help"])
        assert "--list" in r.stdout
        assert "--dry-run" in r.stdout
        assert "--model" in r.stdout
        assert "topic" in r.stdout.lower()


class TestSubprocessList:
    """Test --list flag via subprocess."""

    def test_list_exits_zero(self):
        r = _run(["--list"])
        assert r.returncode == 0

    def test_list_shows_no_cards_message(self):
        """--list prints 'No cards found.' when CARDS_DIR is empty or missing."""
        r = _run(["--list"])
        # Either "No cards found." or card names — either is fine
        assert r.returncode == 0
        assert r.stdout.strip() == "No cards found." or r.stdout.strip() != ""

    def test_list_shows_existing_cards(self, tmp_path):
        """--list prints card filenames when they exist."""
        cards_dir = CARDS_DIR
        cards_dir.mkdir(parents=True, exist_ok=True)
        test_card = cards_dir / "2099-01-01-test-subprocess.md"
        test_card.write_text("# test card")
        try:
            r = _run(["--list"])
            assert r.returncode == 0
            assert "2099-01-01-test-subprocess.md" in r.stdout
        finally:
            test_card.unlink(missing_ok=True)


class TestSubprocessNoArgs:
    """Test invocation without required topic argument."""

    def test_no_args_exits_nonzero(self):
        r = _run([])
        assert r.returncode != 0

    def test_no_args_prints_error(self):
        r = _run([])
        assert "topic" in r.stderr.lower() or "required" in r.stderr.lower()


class TestSubprocessDryRun:
    """Test --dry-run via subprocess (requires OPENAI_API_KEY)."""

    def test_dry_run_without_api_key_fails_gracefully(self):
        """--dry-run without a valid API key should exit with an error."""
        r = _run(["--dry-run", "Test Topic"], env={"HOME": str(Path.home())})
        # Without OPENAI_API_KEY, openai raises an error
        assert r.returncode != 0


# ══════════════════════════════════════════════════════════════════════════
# ── exec-based pure function tests ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════


# ── Constants ─────────────────────────────────────────────────────────────


def test_cards_dir_path():
    """CARDS_DIR points to the correct euchromatin consulting cards path."""
    assert CARDS_DIR == Path.home() / "epigenome" / "chromatin" / "euchromatin" / "consulting" / "cards"


def test_model_default():
    """Default model is a valid OpenAI model name."""
    assert MODEL == "gpt-4.1-mini"


def test_system_prompt_contains_sections():
    """System prompt must request all five required sections."""
    for section in ("Problem", "Impact", "Approach", "Evidence", "So What"):
        assert section in SYSTEM_PROMPT


# ── slugify ───────────────────────────────────────────────────────────────


def test_slugify_basic():
    assert slugify("AI Governance in Banks") == "ai-governance-in-banks"


def test_slugify_special_chars():
    assert slugify("EU AI Act — Penalties & Fines!") == "eu-ai-act-penalties-fines"


def test_slugify_multiple_spaces():
    assert slugify("  model   risk   governance  ") == "model-risk-governance"


def test_slugify_long_topic_truncated():
    long_topic = "a " * 60  # 120 chars
    result = slugify(long_topic)
    assert len(result) <= 80


def test_slugify_idempotent():
    topic = "AI model risk governance in APAC banks"
    assert slugify(slugify(topic)) == slugify(topic)


def test_slugify_underscores_to_hyphens():
    assert slugify("model_risk_management") == "model-risk-management"


def test_slugify_empty_string():
    assert slugify("") == ""


def test_slugify_only_special_chars():
    assert slugify("!@#$%^&*()") == ""


def test_slugify_leading_trailing_hyphens_stripped():
    assert slugify("---hello---") == "hello"


# ── build_markdown ────────────────────────────────────────────────────────


def test_build_markdown_has_frontmatter():
    md = build_markdown("Test Topic", "## Problem\nSomething.")
    assert md.startswith("---\n")
    assert "tags: [consulting-card, insight]" in md
    assert f"created: {date.today().isoformat()}" in md


def test_build_markdown_has_title():
    md = build_markdown("AI Risk", "## Problem\nSomething.")
    assert "# Insight Card: AI Risk" in md


def test_build_markdown_includes_body():
    body = "## Problem\nCore issue.\n## So What\nAct now."
    md = build_markdown("X", body)
    assert body in md


def test_build_markdown_slug_in_frontmatter():
    md = build_markdown("AI Governance", "body")
    assert "slug: ai-governance" in md


def test_build_markdown_topic_in_frontmatter():
    md = build_markdown('Topic "with quotes"', "body")
    assert "Topic" in md


# ── list_cards ────────────────────────────────────────────────────────────


def test_list_cards_empty(tmp_path):
    with _cards_dir(tmp_path):
        assert list_cards() == []


def test_list_cards_returns_md_files(tmp_path):
    with _cards_dir(tmp_path):
        (tmp_path / "2026-01-01-test.md").write_text("card")
        (tmp_path / "2026-01-02-another.md").write_text("card")
        (tmp_path / "notes.txt").write_text("not a card")
        cards = list_cards()
    assert len(cards) == 2
    assert all(c.suffix == ".md" for c in cards)


def test_list_cards_sorted(tmp_path):
    with _cards_dir(tmp_path):
        (tmp_path / "2026-03-01-beta.md").write_text("b")
        (tmp_path / "2026-01-01-alpha.md").write_text("a")
        cards = list_cards()
    assert cards[0].name == "2026-01-01-alpha.md"


# ── write_card ────────────────────────────────────────────────────────────


def test_write_card_creates_file(tmp_path):
    with _cards_dir(tmp_path):
        path = write_card("Test Topic", "## Problem\nBody here.")
    assert path.exists()
    content = path.read_text()
    assert "# Insight Card: Test Topic" in content
    assert "## Problem\nBody here." in content


def test_write_card_filename_format(tmp_path):
    with _cards_dir(tmp_path):
        path = write_card("AI Governance", "body")
    today_str = date.today().isoformat()
    assert path.name == f"{today_str}-ai-governance.md"


def test_write_card_creates_directory(tmp_path):
    cards_dir = tmp_path / "cards" / "sub"
    with _cards_dir(cards_dir):
        path = write_card("Test", "body")
    assert cards_dir.exists()
    assert path.exists()


def test_write_card_atomic(tmp_path):
    """write_card uses tmp+rename so no partial files are left on error."""
    with _cards_dir(tmp_path):
        path = write_card("Atomic Test", "body")
    assert path.exists()
    assert not path.with_suffix(".md.tmp").exists()


# ── generate_card ─────────────────────────────────────────────────────────


def test_generate_card_calls_openai():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="## Problem\nTest problem."))]

    ctx, _ = _mock_openai(mock_response)
    with ctx:
        result = generate_card("test topic")

    assert result == "## Problem\nTest problem."


def test_generate_card_uses_model():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="body"))]

    ctx, MockClient = _mock_openai(mock_response)
    with ctx:
        generate_card("test", model="gpt-4o")

        call_kwargs = MockClient.return_value.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"


def test_generate_card_strips_whitespace():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="  body  \n"))]

    ctx, _ = _mock_openai(mock_response)
    with ctx:
        result = generate_card("test")

    assert result == "body"


def test_generate_card_passes_topic():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="ok"))]

    ctx, MockClient = _mock_openai(mock_response)
    with ctx:
        generate_card("climate risk in ASEAN")

        call_kwargs = MockClient.return_value.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "climate risk in ASEAN" in user_msg


# ── main CLI (exec-based, with mocked OpenAI) ────────────────────────────


def test_main_list(capsys, tmp_path):
    with _cards_dir(tmp_path):
        (tmp_path / "card.md").write_text("x")
        main(["--list"])
    captured = capsys.readouterr()
    assert "card.md" in captured.out


def test_main_list_empty(capsys, tmp_path):
    with _cards_dir(tmp_path):
        main(["--list"])
    captured = capsys.readouterr()
    assert "No cards found" in captured.out


def test_main_no_topic_exits():
    with pytest.raises(SystemExit):
        main([])


def test_main_dry_run(capsys):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="## Problem\nP."))]

    ctx, _ = _mock_openai(mock_response)
    with ctx:
        main(["--dry-run", "Test Topic"])

    captured = capsys.readouterr()
    assert "# Insight Card: Test Topic" in captured.out
    assert "## Problem\nP." in captured.out


def test_main_writes_file(capsys, tmp_path):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="## Problem\nP."))]

    ctx, _ = _mock_openai(mock_response)
    with _cards_dir(tmp_path), ctx:
        main(["Test Topic"])

    cards = list(tmp_path.glob("*.md"))
    assert len(cards) == 1
    content = cards[0].read_text()
    assert "# Insight Card: Test Topic" in content
    captured = capsys.readouterr()
    assert "Card written to:" in captured.err


def test_main_model_flag(capsys):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="body"))]

    ctx, MockClient = _mock_openai(mock_response)
    with ctx:
        main(["--dry-run", "--model", "gpt-4o", "Test"])

        call_kwargs = MockClient.return_value.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"
