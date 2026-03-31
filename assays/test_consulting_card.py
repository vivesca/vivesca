from __future__ import annotations

"""Tests for consulting-card effector — insight card generator."""

import argparse
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module():
    """Load consulting-card via exec (effector pattern, not importable).

    The effector imports ``openai`` at load time.  Inject a stub module so
    the exec succeeds even when the ``openai`` package is not installed.
    """
    source = open("/home/terry/germline/effectors/consulting-card.py").read()
    import types
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = MagicMock()
    ns: dict = {
        "__name__": "consulting_card",
        "__file__": "/home/terry/germline/effectors/consulting-card.py",
        "openai": openai_stub,
    }
    exec(source, ns)
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

    The effector does ``from openai import OpenAI`` at load time, so the
    name lives in _ns.  Patching ``openai.OpenAI`` won't reach it.
    """
    MockClient = MagicMock()
    MockClient.return_value.chat.completions.create.return_value = mock_response
    return patch.dict(_ns, {"OpenAI": MockClient}), MockClient


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


# ── generate_card ─────────────────────────────────────────────────────────


def test_generate_card_calls_openai():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="## Problem\nTest problem."))]

    with _mock_openai(mock_response)[0]:
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

    with _mock_openai(mock_response)[0]:
        result = generate_card("test")

    assert result == "body"


# ── main CLI ──────────────────────────────────────────────────────────────


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

    with _mock_openai(mock_response)[0]:
        main(["--dry-run", "Test Topic"])

    captured = capsys.readouterr()
    assert "# Insight Card: Test Topic" in captured.out
    assert "## Problem\nP." in captured.out


def test_main_writes_file(capsys, tmp_path):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="## Problem\nP."))]

    with _cards_dir(tmp_path), _mock_openai(mock_response)[0]:
        main(["Test Topic"])

    cards = list(tmp_path.glob("*.md"))
    assert len(cards) == 1
    content = cards[0].read_text()
    assert "# Insight Card: Test Topic" in content
    captured = capsys.readouterr()
    assert "Card written to:" in captured.err
