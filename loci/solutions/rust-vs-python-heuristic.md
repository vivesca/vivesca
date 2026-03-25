# Rust vs Python — Decision Heuristic for New Tools

## One-liner

If the tool *does work* (computation, parsing, data processing) → Rust.
If the tool *calls things that do work* (API glue, orchestration, AI pipelines) → Python.

## Decision Table

| Signal | Rust | Python |
|--------|------|--------|
| Core logic is HTTP calls + JSON parsing | Either | Either |
| Needs ML/AI libraries (LangGraph, torch, etc.) | — | Python |
| Binary distribution matters (share with others) | Rust | — |
| Startup speed matters (called 100x/day) | Rust | — |
| Heavy string/data processing | Rust | — |
| Rapid prototyping, design still evolving | — | Python |
| Existing Cargo workspace has shared deps | Rust | — |
| `uv run --script` with inline deps is sufficient | — | Python |
| Does real computation (parsing, diffing) | Rust | — |
| Mostly glue between APIs | — | Python |
| Zero environment issues needed | Rust | — |
| Might throw it away | — | Python |
| Client/team handover needed | — | Python |

## Fleet Policy

- **Existing Rust tools** (deltos, speculor, poros, etc.) — keep as-is. Don't rewrite.
- **New personal tools** — default Python unless a specific Rust reason exists.
- **Capco/client work** — always Python. Clients are Python shops, handover matters.
- **LRN-20260313-001**: The fleet will naturally drift toward Python as work shifts to consulting. Don't fight it.
