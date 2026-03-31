"""Tests for prompt templates."""

from metabolon.codons.templates import research, compose_signal, morning_brief


def test_research_basic():
    result = research(topic="AI governance")
    assert "AI governance" in result
    assert "Executive Summary" in result


def test_research_with_context():
    result = research(topic="HKMA", context="banking regulation")
    assert "banking regulation" in result


def test_research_depth_quick():
    result = research(topic="test", depth="quick")
    assert "quick" in result.lower()


def test_research_depth_deep():
    result = research(topic="test", depth="deep")
    assert "deep" in result.lower()


def test_compose_signal_email():
    result = compose_signal(platform="email", recipient="John", intent="follow up")
    assert "John" in result
    assert "subject line" in result.lower()


def test_compose_signal_whatsapp():
    result = compose_signal(platform="whatsapp", recipient="Jane", intent="say hi")
    assert "WhatsApp" in result


def test_compose_signal_linkedin():
    result = compose_signal(platform="linkedin", recipient="Bob", intent="connect")
    assert "LinkedIn" in result


def test_compose_signal_with_context():
    result = compose_signal(platform="email", recipient="X", intent="Y", context="met at conf")
    assert "met at conf" in result


def test_morning_brief_basic():
    result = morning_brief()
    assert "calendar" in result.lower() or "schedule" in result.lower()
    assert "Jeeves" in result


def test_morning_brief_with_focus():
    result = morning_brief(focus="Capco prep")
    assert "Capco prep" in result


def test_morning_brief_with_budget():
    result = morning_brief(include_budget=True)
    assert "budget" in result.lower()
