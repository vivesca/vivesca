#!/usr/bin/env python3
"""LangGraph-based translation agent for Temporal worker.

Replaces raw `claude --print` subprocess with a structured agent graph:
  plan → execute (tool loop) → verify → review

Uses provider's Anthropic-compatible API (ZhiPu, etc.) via langchain-anthropic.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Annotated

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

REVIEW_LOG = Path.home() / "germline" / "loci" / "ribosome-reviews.jsonl"

# ── Provider configs ──

PROVIDER_CONFIGS = {
    "zhipu": {
        "model": "GLM-5.1",
        "api_key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/anthropic",
    },
    "infini": {
        "model": "minimax-m2.7",
        "api_key_env": "INFINI_API_KEY",
        "base_url": "https://cloud.infini-ai.com/maas/coding",
    },
    "volcano": {
        "model": "doubao-seed-2.0-code",
        "api_key_env": "VOLCANO_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/coding",
    },
    "codex": {
        "model": "gpt-5.4",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None,  # uses native OpenAI endpoint
    },
}

# ── Tools the agent can use ──


@tool
def run_shell(command: str) -> str:
    """Run a shell command and return stdout+stderr. Use for file ops, git, etc."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path.home()),
        )
        output = result.stdout + result.stderr
        return output[:4000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 60s"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        p = Path(path).expanduser()
        content = p.read_text()
        return content[:8000] if content else "(empty file)"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"OK: wrote {len(content)} bytes to {p}"
    except Exception as e:
        return f"ERROR: {e}"


TOOLS = [run_shell, read_file, write_file]
TOOL_MAP = {t.name: t for t in TOOLS}

# ── State ──


class TranslationState(TypedDict):
    messages: Annotated[list, add_messages]
    task: str
    provider: str
    plan: str
    verification: str
    review: dict
    tool_calls_count: int


# ── Nodes ──

SYSTEM_PROMPT = """You are a ribosome — a task execution agent. You receive a task and execute it precisely.

Rules:
- Read files BEFORE modifying them. Never rewrite a file from memory.
- When editing a file, preserve ALL existing content unless told to remove something.
- After modifying a file, read it back to verify.
- If a file doesn't exist and the task says to edit it, report failure — don't create from scratch unless told to.
- Be surgical: change only what the task requires.
"""


def _get_llm(provider: str) -> ChatZhipuAI:
    """Create LLM client for the given provider.

    All Anthropic-compatible providers (zhipu, infini, volcano) route through
    ChatZhipuAI with ZHIPUAI_API_KEY + base_url override. The class name is
    misleading but the wire protocol is identical.
    """
    config = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["zhipu"])
    api_key = os.environ.get(config["api_key_env"], "")
    if not api_key:
        raise ValueError(f"No API key found in env var {config['api_key_env']}")
    # ChatZhipuAI reads ZHIPUAI_API_KEY from env — set it regardless of provider
    os.environ["ZHIPUAI_API_KEY"] = api_key
    kwargs: dict = {"model": config["model"], "temperature": 0.1}
    if config.get("base_url"):
        kwargs["zhipuai_api_base"] = config["base_url"]
    return ChatZhipuAI(**kwargs)


def plan_node(state: TranslationState) -> dict:
    """Plan the task execution."""
    llm = _get_llm(state["provider"])
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Plan the execution of this task step by step. Be concise.\n\nTask: {state['task']}"
            ),
        ]
    )
    plan = response.content if isinstance(response.content, str) else str(response.content)
    return {
        "plan": plan,
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Execute this task. Follow your plan.\n\nTask: {state['task']}\n\nPlan:\n{plan}"
            ),
        ],
    }


def execute_node(state: TranslationState) -> dict:
    """Execute with tool calling loop."""
    llm = _get_llm(state["provider"]).bind_tools(TOOLS)
    messages = list(state["messages"])
    response = llm.invoke(messages)
    messages.append(response)

    tool_calls_count = state.get("tool_calls_count", 0)

    # Process tool calls
    if response.tool_calls:
        tool_messages = []
        for tc in response.tool_calls:
            tool_fn = TOOL_MAP.get(tc["name"])
            if tool_fn:
                result = tool_fn.invoke(tc["args"])
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                tool_calls_count += 1
            else:
                tool_messages.append(
                    ToolMessage(content=f"Unknown tool: {tc['name']}", tool_call_id=tc["id"])
                )
        messages.extend(tool_messages)

    return {"messages": messages, "tool_calls_count": tool_calls_count}


def should_continue(state: TranslationState) -> str:
    """Decide whether to continue tool calling or move to verify."""
    messages = state["messages"]
    last_ai = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai = msg
            break

    # Stop if no more tool calls, or hit 15 tool call limit
    if last_ai and not last_ai.tool_calls:
        return "verify"
    if state.get("tool_calls_count", 0) >= 15:
        return "verify"
    return "execute"


def verify_node(state: TranslationState) -> dict:
    """Verify the work was done correctly."""
    llm = _get_llm(state["provider"])
    messages = list(state["messages"])
    messages.append(
        HumanMessage(
            content="Verify your work. Read back any files you modified. "
            "Report: (1) what was done, (2) what changed, (3) any concerns. Be concise."
        )
    )
    response = llm.bind_tools(TOOLS).invoke(messages)
    messages.append(response)

    # Let it use tools to verify
    if response.tool_calls:
        for tc in response.tool_calls:
            tool_fn = TOOL_MAP.get(tc["name"])
            if tool_fn:
                result = tool_fn.invoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        # Get final verification summary
        response2 = llm.invoke(messages)
        messages.append(response2)
        verification = (
            response2.content if isinstance(response2.content, str) else str(response2.content)
        )
    else:
        verification = (
            response.content if isinstance(response.content, str) else str(response.content)
        )

    return {"messages": messages, "verification": verification}


def review_node(state: TranslationState) -> dict:
    """Review the result for quality signals."""
    verification = state.get("verification", "")
    tool_calls = state.get("tool_calls_count", 0)
    task = state.get("task", "")

    flags: list[str] = []

    # Check for destruction signals
    for keyword in ["replaced entire", "overwrote", "deleted all", "rm -rf", "wrote 0 bytes"]:
        if keyword.lower() in verification.lower():
            flags.append(f"destruction: {keyword}")

    # Check for error signals
    for keyword in ["SyntaxError", "ImportError", "PermissionError", "FAILED", "ERROR"]:
        if keyword in verification:
            flags.append(f"error: {keyword}")

    # No tool calls = agent didn't do anything
    if tool_calls == 0:
        flags.append("no_tool_calls")

    # Suspiciously few tool calls for complex task
    task_words = len(task.split())
    if task_words > 30 and tool_calls < 3:
        flags.append(f"thin_execution: {tool_calls} tools for {task_words}-word task")

    approved = not any(f.startswith("destruction") for f in flags) and tool_calls > 0
    verdict = (
        "approved" if approved and not flags else "approved_with_flags" if approved else "rejected"
    )

    review = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "task": task[:200],
        "provider": state.get("provider", ""),
        "tool_calls": tool_calls,
        "flags": flags,
        "verdict": verdict,
        "approved": approved,
        "verification_len": len(verification),
    }

    # Persist
    try:
        REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_LOG, "a") as f:
            f.write(json.dumps(review) + "\n")
    except OSError:
        pass

    return {"review": review}


# ── Build graph ──


def build_translation_graph():
    """Build and compile the translation agent graph."""
    graph = StateGraph(TranslationState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("verify", verify_node)
    graph.add_node("review", review_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges(
        "execute", should_continue, {"execute": "execute", "verify": "verify"}
    )
    graph.add_edge("verify", "review")
    graph.add_edge("review", END)

    return graph.compile()


# ── Entry point for Temporal activity ──


def run_translation_graph(task: str, provider: str = "zhipu") -> dict:
    """Run the translation graph synchronously. Called from Temporal activity."""
    graph = build_translation_graph()

    result = graph.invoke(
        {
            "task": task,
            "provider": provider,
            "messages": [],
            "plan": "",
            "verification": "",
            "review": {},
            "tool_calls_count": 0,
        }
    )

    review = result.get("review", {})
    verification = result.get("verification", "")
    plan = result.get("plan", "")

    return {
        "task": task[:200],
        "provider": provider,
        "success": review.get("verdict", "rejected") != "rejected",
        "exit_code": 0 if review.get("verdict") != "rejected" else 1,
        "stdout": f"Plan:\n{plan[:1000]}\n\nVerification:\n{verification[:2000]}",
        "stderr": "",
        "review": review,
    }
