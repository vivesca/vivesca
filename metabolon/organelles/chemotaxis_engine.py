"""chemotaxis_engine — web search via Perplexity API (formerly noesis).

Endosymbiosis: Rust binary → Python organelle.
Credentials: PERPLEXITY_API_KEY env var.
"""

import json
import os
import urllib.request

_API_URL = "https://api.perplexity.ai/chat/completions"
_MODELS = {
    "search": "sonar",
    "ask": "sonar-pro",
    "research": "sonar-deep-research",
}


def _api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        raise ValueError("PERPLEXITY_API_KEY not set")
    return key


def _query(model: str, query: str, timeout: int = 300) -> str:
    """Query Perplexity API and return synthesised text."""
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer accurately based on what you can find. "
                        "If you cannot confirm specific facts, say explicitly "
                        "that you could not confirm it. Distinguish between "
                        "'not found in results' and 'does not exist'."
                    ),
                },
                {"role": "user", "content": query},
            ],
        }
    ).encode()

    req = urllib.request.Request(
        _API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]

    # Append citations if available
    citations = result.get("citations", [])
    if citations:
        content += "\n\nSources:\n" + "\n".join(f"- {c}" for c in citations)

    return content


def recall(query: str) -> str:
    """Quick gradient sensing (~$0.006)."""
    return _query(_MODELS["search"], query, timeout=30)


def ask(query: str) -> str:
    """Thorough environmental survey (~$0.01)."""
    return _query(_MODELS["ask"], query, timeout=60)


def research(query: str, save_path: str = "") -> str:
    """Deep chemotactic exploration (~$0.40). EXPENSIVE."""
    result = _query(_MODELS["research"], query, timeout=300)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            f.write(result)
    return result
