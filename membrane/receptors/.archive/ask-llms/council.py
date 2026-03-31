#!/usr/bin/env python3
from __future__ import annotations

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx",
# ]
# ///
"""
Multi-LLM Query Tool

Query multiple LLMs in parallel via OpenRouter and display their responses.
A simplified version of LLM Council for quick comparisons.

Usage:
    uv run council.py "What is the best way to handle errors in Python?"
    uv run council.py "your question" --cheap
    uv run council.py "your question" --models "openai/gpt-4o,anthropic/claude-sonnet-4"
"""

import argparse
import asyncio
import os
import sys

import httpx

# Expensive models (2026 frontier with thinking)
EXPENSIVE_MODELS = [
    "anthropic/claude-opus-4.5",
    "openai/gpt-5.2",
    "google/gemini-3-pro-preview",
    "x-ai/grok-4",
    "deepseek/deepseek-r1",
]

# Cheap models (fast and affordable)
CHEAP_MODELS = [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-4o",
    "google/gemini-2.0-flash-001",
    "x-ai/grok-4.1-fast",
    "deepseek/deepseek-v3.2",
]

# Models that support reasoning/thinking mode
REASONING_MODELS = {
    "anthropic/claude-opus-4.5",
    "openai/gpt-5.2",
    "google/gemini-3-pro-preview",
    "google/gemini-2.5-pro",
    "x-ai/grok-4",
    "deepseek/deepseek-r1",
}

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def query_model(
    client: httpx.AsyncClient,
    model: str,
    question: str,
    api_key: str,
    timeout: float = 60.0,
    enable_thinking: bool = False,
) -> tuple[str, str | None, str | None]:
    """
    Query a single model via OpenRouter API.

    Returns:
        Tuple of (model_name, response_content, error_message)
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
    }

    # Enable reasoning for supported models
    if enable_thinking and model in REASONING_MODELS:
        payload["reasoning"] = {"effort": "high"}

    try:
        response = await client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return (model, content, None)

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        return (model, None, error_msg)
    except httpx.TimeoutException:
        return (model, None, f"Timeout after {timeout}s")
    except Exception as e:
        return (model, None, str(e))


async def query_all_models(
    question: str,
    models: list[str],
    api_key: str,
    timeout: float = 60.0,
    enable_thinking: bool = False,
) -> list[tuple[str, str | None, str | None]]:
    """Query all models in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [
            query_model(client, model, question, api_key, timeout, enable_thinking)
            for model in models
        ]
        return await asyncio.gather(*tasks)


def print_results(results: list[tuple[str, str | None, str | None]]) -> int:
    """Print results and return exit code (0 if any succeeded, 1 if all failed)."""
    success_count = 0

    for model, content, error in results:
        print("=" * 60)
        print(model)
        print("=" * 60)

        if content:
            print(content)
            success_count += 1
        else:
            print(f"[ERROR] {error}")

        print()

    return 0 if success_count > 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Query multiple LLMs in parallel via OpenRouter")
    parser.add_argument("question", help="The question to ask all models")
    parser.add_argument(
        "--models",
        help="Comma-separated list of model identifiers",
        default=None,
    )
    parser.add_argument(
        "--cheap",
        action="store_true",
        help="Use cheaper/faster models (claude-sonnet, gpt-4o, gemini-flash)",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Disable reasoning/thinking mode for expensive models",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds per model (default: 60 for cheap, 180 for expensive)",
    )
    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        print("Get your API key at https://openrouter.ai", file=sys.stderr)
        sys.exit(1)

    # Select models
    if args.models:
        models = [m.strip() for m in args.models.split(",")]
        enable_thinking = not args.no_thinking
        timeout = args.timeout or 120.0
    elif args.cheap:
        models = CHEAP_MODELS
        enable_thinking = False
        timeout = args.timeout or 60.0
    else:
        models = EXPENSIVE_MODELS
        enable_thinking = not args.no_thinking
        timeout = args.timeout or 180.0

    mode = (
        "cheap" if args.cheap else ("expensive" if enable_thinking else "expensive (no thinking)")
    )
    print(f"Querying {len(models)} models [{mode}]...")
    print(f"Question: {args.question[:100]}{'...' if len(args.question) > 100 else ''}")
    if enable_thinking:
        print("Thinking mode: enabled")
    print()

    # Run queries
    results = asyncio.run(
        query_all_models(args.question, models, api_key, timeout, enable_thinking)
    )

    # Print and exit
    exit_code = print_results(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
