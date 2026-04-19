"""Provider abstraction — build CLI commands for each harness type."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mtor.config import ProviderConfig


@dataclass
class ProviderCommand:
    args: list[str]
    env: dict[str, str]
    timeout: int


def build_command(provider: ProviderConfig, prompt: str, timeout: int = 7200) -> ProviderCommand:
    api_key = provider.api_key
    if not api_key:
        raise ValueError(f"Provider {provider.name}: env var {provider.key_env} not set")
    env = dict(os.environ)
    if provider.harness == "claude":
        env.update(
            {
                "ANTHROPIC_API_KEY": api_key,
                "ANTHROPIC_BASE_URL": provider.url,
                "ANTHROPIC_DEFAULT_SONNET_MODEL": provider.model,
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "API_TIMEOUT_MS": "3000000",
            }
        )
        args = [
            "claude",
            "--print",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "-p",
            prompt,
        ]
    elif provider.harness == "codex":
        env["OPENAI_API_KEY"] = api_key
        args = [
            "codex",
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            prompt,
        ]
    elif provider.harness == "gemini":
        env.update({"GEMINI_API_KEY": api_key, "GOOGLE_API_KEY": api_key})
        args = ["gemini", "--sandbox=false", "--yolo", "-p", prompt]
    elif provider.harness == "goose":
        env.update({"ANTHROPIC_API_KEY": api_key, "ANTHROPIC_HOST": provider.url})
        args = [
            "goose",
            "run",
            "-q",
            "--no-session",
            "--provider",
            "anthropic",
            "--model",
            provider.model,
            "-t",
            prompt,
        ]
    elif provider.harness == "droid":
        env[f"{provider.name.upper()}_API_KEY"] = api_key
        args = ["droid", "exec", "--auto", "full", "-m", provider.model, prompt]
    else:
        raise ValueError(f"Unknown harness: {provider.harness}")
    return ProviderCommand(args=args, env=env, timeout=timeout)
