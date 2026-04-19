import pytest
from mtor.config import ProviderConfig
from mtor.providers import build_command


def _make_provider(harness="claude", name="test"):
    return ProviderConfig(
        name=name,
        url="https://example.com/v1",
        model="test-model",
        key_env="TEST_MTOR_KEY",
        harness=harness,
    )


def test_claude_command(monkeypatch):
    monkeypatch.setenv("TEST_MTOR_KEY", "sk-test")
    cmd = build_command(_make_provider("claude"), "fix the bug")
    assert cmd.args[0] == "claude"
    assert "--print" in cmd.args
    assert cmd.env["ANTHROPIC_API_KEY"] == "sk-test"


def test_codex_command(monkeypatch):
    monkeypatch.setenv("TEST_MTOR_KEY", "sk-test")
    cmd = build_command(_make_provider("codex"), "fix the bug")
    assert cmd.args[0] == "codex"


def test_missing_key():
    with pytest.raises(ValueError, match="not set"):
        build_command(_make_provider("claude"), "fix the bug")


def test_unknown_harness(monkeypatch):
    monkeypatch.setenv("TEST_MTOR_KEY", "sk-test")
    with pytest.raises(ValueError, match="Unknown harness"):
        build_command(_make_provider("unknown"), "fix the bug")
