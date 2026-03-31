"""Unit tests for codons/templates.py prompt functions.

Tests focus on return value structure, edge cases, and parameter handling.
"""

import pytest

from metabolon.codons.templates import research, compose_signal, morning_brief


class TestResearchPrompt:
    """Unit tests for research() prompt generation."""

    def test_returns_string(self):
        result = research(topic="test")
        assert isinstance(result, str)

    def test_topic_included(self):
        result = research(topic="machine learning")
        assert "machine learning" in result

    def test_default_depth_standard(self):
        result = research(topic="test")
        assert "thorough" in result.lower()

    def test_depth_quick_includes_quick_lookup(self):
        result = research(topic="test", depth="quick")
        assert "quick" in result.lower()
        assert "factual lookup" in result.lower()

    def test_depth_deep_includes_expensive_warning(self):
        result = research(topic="test", depth="deep")
        assert "deep" in result.lower()
        assert "expensive" in result.lower()

    def test_unknown_depth_uses_standard(self):
        result = research(topic="test", depth="invalid")
        assert "thorough" in result.lower()

    def test_context_included_when_provided(self):
        result = research(topic="AI", context="Hong Kong regulations")
        assert "Hong Kong regulations" in result

    def test_context_block_not_included_when_empty(self):
        result = research(topic="test", context="")
        assert "Background context:" not in result

    def test_output_format_sections(self):
        result = research(topic="test")
        assert "Executive Summary" in result
        assert "Key Findings" in result
        assert "Sources" in result
        assert "Recommended Next Steps" in result

    def test_concise_instruction(self):
        result = research(topic="test")
        assert "concise" in result.lower()


class TestComposeSignalPrompt:
    """Unit tests for compose_signal() prompt generation."""

    def test_returns_string(self):
        result = compose_signal(platform="email", recipient="John", intent="follow up")
        assert isinstance(result, str)

    def test_recipient_included(self):
        result = compose_signal(platform="email", recipient="Alice", intent="hello")
        assert "Alice" in result

    def test_intent_included(self):
        result = compose_signal(platform="email", recipient="X", intent="schedule meeting")
        assert "schedule meeting" in result

    def test_default_tone_professional(self):
        result = compose_signal(platform="email", recipient="X", intent="Y")
        assert "professional" in result.lower()

    def test_custom_tone_included(self):
        result = compose_signal(platform="email", recipient="X", intent="Y", tone="casual")
        assert "casual" in result.lower()

    def test_platform_whatsapp_description(self):
        result = compose_signal(platform="whatsapp", recipient="X", intent="Y")
        assert "WhatsApp" in result
        assert "casual register" in result

    def test_platform_linkedin_description(self):
        result = compose_signal(platform="linkedin", recipient="X", intent="Y")
        assert "LinkedIn" in result
        assert "150 words max" in result

    def test_platform_email_subject_requirement(self):
        result = compose_signal(platform="email", recipient="X", intent="Y")
        assert "subject line" in result.lower()

    def test_platform_telegram_description(self):
        result = compose_signal(platform="telegram", recipient="X", intent="Y")
        assert "Telegram" in result
        assert "markdown" in result.lower()

    def test_unknown_platform_fallback(self):
        result = compose_signal(platform="slack", recipient="X", intent="Y")
        assert "slack" in result.lower()
        assert "match platform norms" in result.lower()

    def test_context_included_when_provided(self):
        result = compose_signal(platform="email", recipient="X", intent="Y", context="met yesterday")
        assert "met yesterday" in result

    def test_context_block_not_included_when_empty(self):
        result = compose_signal(platform="email", recipient="X", intent="Y", context="")
        assert "\nContext:" not in result

    def test_terry_voice_requirement(self):
        result = compose_signal(platform="email", recipient="X", intent="Y")
        assert "Terry" in result
        assert "direct" in result.lower()

    def test_front_stage_copy_requirement(self):
        result = compose_signal(platform="email", recipient="X", intent="Y")
        assert "front-stage" in result.lower()
        assert "review" in result.lower()

    def test_no_meta_commentary(self):
        result = compose_signal(platform="email", recipient="X", intent="Y")
        assert "meta-commentary" in result.lower()


class TestMorningBriefPrompt:
    """Unit tests for morning_brief() prompt generation."""

    def test_returns_string(self):
        result = morning_brief()
        assert isinstance(result, str)

    def test_calendar_step_included(self):
        result = morning_brief()
        assert "calendar" in result.lower()
        assert "today" in result.lower()

    def test_jeeves_tone(self):
        result = morning_brief()
        assert "Jeeves" in result
        assert "formal yet warm" in result.lower()

    def test_histone_search_step(self):
        result = morning_brief()
        assert "histone_search" in result

    def test_tonus_check(self):
        result = morning_brief()
        assert "Tonus.md" in result

    def test_focus_included_when_provided(self):
        result = morning_brief(focus="Project Alpha")
        assert "Project Alpha" in result
        assert "focus area" in result.lower()

    def test_focus_block_not_included_when_empty(self):
        result = morning_brief(focus="")
        assert "focus area:" not in result.lower()

    def test_budget_not_included_by_default(self):
        result = morning_brief()
        assert "budget" not in result.lower()

    def test_budget_included_when_requested(self):
        result = morning_brief(include_budget=True)
        assert "budget" in result.lower()
        assert "token" in result.lower()

    def test_word_limit(self):
        result = morning_brief()
        assert "300 words" in result

    def test_schedule_section(self):
        result = morning_brief()
        assert "schedule" in result.lower()
        assert "events" in result.lower()

    def test_priorities_section(self):
        result = morning_brief()
        assert "Top 3 priorities" in result or "priorities" in result.lower()

    def test_hkt_timezone(self):
        result = morning_brief()
        assert "HKT" in result

    def test_no_emoji_instruction(self):
        result = morning_brief()
        assert "no emoji" in result.lower()

    def test_prose_over_bullets(self):
        result = morning_brief()
        assert "prose over bullets" in result.lower()
