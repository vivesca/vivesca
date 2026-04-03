"""Integration-level tests for metabolon.codons.templates.

Focuses on decorator metadata, statelessness, special-character handling,
and structural guarantees that the unit-test files don't cover.
"""

import pytest

from metabolon.codons.templates import research, compose_signal, morning_brief


# ── Prompt decorator metadata ──────────────────────────────────────────

class TestPromptMetadata:
    """Verify the @prompt decorator exposes correct MCP metadata."""

    def test_research_has_prompt_name(self):
        assert research.__fastmcp__.name == "research"

    def test_compose_signal_has_prompt_name(self):
        assert compose_signal.__fastmcp__.name == "compose_signal"

    def test_morning_brief_has_prompt_name(self):
        assert morning_brief.__fastmcp__.name == "morning_brief"

    def test_research_description_mentions_rheotaxis(self):
        assert "rheotaxis_search" in research.__fastmcp__.description

    def test_compose_signal_description_mentions_voice(self):
        assert "Terry" in compose_signal.__fastmcp__.description
        assert "front-stage" in compose_signal.__fastmcp__.description

    def test_morning_brief_description_mentions_calendar(self):
        assert "calendar" in morning_brief.__fastmcp__.description


# ── Statelessness ──────────────────────────────────────────────────────

class TestStatelessness:
    """Repeated calls with same args must produce identical output."""

    def test_research_idempotent(self):
        a = research(topic="token budgets")
        b = research(topic="token budgets")
        assert a == b

    def test_compose_signal_idempotent(self):
        a = compose_signal(platform="email", recipient="A", intent="B")
        b = compose_signal(platform="email", recipient="A", intent="B")
        assert a == b

    def test_morning_brief_idempotent(self):
        a = morning_brief()
        b = morning_brief()
        assert a == b


# ── Special characters & edge inputs ───────────────────────────────────

class TestSpecialInputs:
    """Functions must handle unusual inputs without raising."""

    def test_research_topic_with_special_chars(self):
        result = research(topic="AI & governance: a 2026 perspective (v2)")
        assert "AI & governance: a 2026 perspective (v2)" in result

    def test_research_topic_with_newlines(self):
        result = research(topic="multi\nline\ntopic")
        assert "multi\nline\ntopic" in result

    def test_compose_signal_recipient_with_unicode(self):
        result = compose_signal(
            platform="email",
            recipient="José García",
            intent="reunión",
        )
        assert "José García" in result

    def test_morning_brief_focus_with_special_chars(self):
        result = morning_brief(focus="Q3 review & board prep (async)")
        assert "Q3 review & board prep (async)" in result


# ── Structural guarantees ──────────────────────────────────────────────

class TestStructuralGuarantees:
    """Verify cross-cutting structural properties of all templates."""

    @pytest.mark.parametrize(
        "fn,kwargs",
        [
            (research, {"topic": "x"}),
            (compose_signal, {"platform": "email", "recipient": "Y", "intent": "Z"}),
            (morning_brief, {}),
        ],
    )
    def test_return_is_nonempty_string(self, fn, kwargs):
        result = fn(**kwargs)
        assert isinstance(result, str)
        assert len(result) > 50  # real prompts are substantial

    @pytest.mark.parametrize(
        "fn,kwargs",
        [
            (research, {"topic": "x"}),
            (compose_signal, {"platform": "email", "recipient": "Y", "intent": "Z"}),
            (morning_brief, {}),
        ],
    )
    def test_return_does_not_double_newlines_excessively(self, fn, kwargs):
        result = fn(**kwargs)
        assert "\n\n\n" not in result

    def test_all_depth_values_return_content(self):
        for depth in ("quick", "standard", "deep"):
            result = research(topic="test", depth=depth)
            assert len(result) > 50, f"depth={depth} produced too-short output"

    def test_all_known_platforms_return_content(self):
        for platform in ("whatsapp", "linkedin", "email", "telegram"):
            result = compose_signal(
                platform=platform, recipient="X", intent="hello",
            )
            assert platform in result.lower()
