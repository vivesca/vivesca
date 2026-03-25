---
name: LangGraph vs Plain Python for Batch Pipelines
description: Research on whether LangGraph earns its keep for scheduled, non-interactive batch pipelines. Verdict: no for thalamus-style pipelines.
type: reference
---

## Verdict
LangGraph does NOT earn its keep for a scheduled batch pipeline like thalamus v2. Its value propositions (persistence/checkpointing, human-in-the-loop, streaming, long-running stateful agents) are all irrelevant to cron-triggered, no-HITL, subprocess-based pipelines. The three features it does offer (state container, conditional routing, retry loops) are ~20 lines of plain Python each.

## Useful LangGraph Features (and their plain Python equivalents)
- StateGraph / TypedDict state: replaced by a plain dataclass or TypedDict dict passed between functions
- Conditional edges: replaced by `if/elif` after a node function returns
- Retry loops with max_attempts counter: replaced by a `for attempt in range(max_retries)` loop

## Irrelevant Features (framework tax paid for nothing)
- Checkpointing / persistence (SQLite/Postgres) — thalamus runs to completion, no resume needed
- Human-in-the-loop / interrupts — unattended cron, no human present
- Streaming output — no consumer
- LangSmith observability integration — not using LangSmith
- LangGraph Platform / server — running as a CLI, not a server
- Async/concurrent node execution — subprocess calls are already sequential
- Thread management — no multi-session state

## Dependency Tax
Core langgraph 1.1.2 pulls in: langchain-core, langgraph-checkpoint, langgraph-sdk, langgraph-prebuilt, langgraph-prebuilt, xxhash, pydantic, ormsgpack. Transitively this is the entire langchain-core ecosystem. Not catastrophic but meaningful for a cron script.

## Version Stability
LangGraph 1.0 (Nov 2025) committed to no breaking changes until 2.0. Pre-1.0 history was messy (0.1→0.2→0.3 breaking cycles). Now stabilised but the history is a yellow flag for long-lived scripts.

## Practitioner Consensus
HN thread (id=40739982): "death by abstraction," 5 layers to change a detail, teams reverting to direct API calls. Latenode community: "wrestling against the up-front graph structure" for dynamic control flow. ZenML alternatives post: single-threaded design, API instability, over-abstraction. One measured case: 40% latency reduction after removing LangChain for high-volume work.

## Where LangGraph Genuinely Wins
- Multi-agent systems where agents interrupt each other
- Long-running sessions needing resume-from-checkpoint
- Human review gates mid-execution
- Concurrent node execution (Pregel supersteps)
- Visualization of complex agent topologies
- LangSmith integration for observability

## Key Sources
- https://news.ycombinator.com/item?id=40739982 (HN: Why we no longer use LangChain)
- https://www.zenml.io/blog/langgraph-alternatives
- https://community.latenode.com/t/why-are-langchain-and-langgraph-still-so-complex-to-work-with-in-2025/39049
- https://dylancastillo.co/posts/agentic-workflows-langgraph.html
- https://pypi.org/project/langgraph/ (v1.1.2, Mar 12 2026)
- https://deepwiki.com/langchain-ai/langgraph/2-core-architecture
