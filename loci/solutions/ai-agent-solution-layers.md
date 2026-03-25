# AI Agent Solution Layer Framework

A four-layer anchor for designing and communicating any AI agent solution.

## The Four Layers

1. **Interaction / Interface layer** — chat, API endpoint, voice, webhook, scheduled trigger. Not "chat" — naming it chat constrains what can plug in.
2. **Model inference layer** — the LLM call itself. Different vendor lock-in risk from orchestration.
3. **Orchestration layer** — control flow: routing, sequencing, agent handoffs, retry logic. Distinct from tooling: when a subagent is spawned, that's orchestration, not tooling.
4. **Tooling layer** — external actions: APIs, DBs, file ops, retrieval, RAG, vector search. Data/retrieval lives here as a named sub-layer, not a separate tier.

## Key Design Decisions

**Memory/state:** Cross-cutting concern — doesn't fit neatly into any layer. Design it explicitly; don't let it scatter. "Cross-cutting" without a named owner and enforcement mechanism is just "optional" — someone will own it or nobody will.

**Data/retrieval:** Fold into tooling. RAG is a tool call. Separating it is a slide concern, not an architecture concern. Call it out as a sub-layer when the audience cares (data engineers, CDOs). "Tooling includes retrieval and data grounding."

**Why four layers:** Each has a different vendor lock-in risk and evolves at a different rate. Clean swap-out points. Five+ layers starts to feel like a framework pitch.

## Enforcement at the Seams

The four layers are necessary but not sufficient. Each boundary between layers needs an explicit enforcement mechanism — not a design principle, a named owner and a gate:

- **Interaction → Orchestration:** authentication, rate limiting, input validation
- **Orchestration → Inference:** prompt injection detection, PII handling, context scoping
- **Orchestration → Tooling:** capability checks, access control, pre-execution authorization

These are architectural concerns, not a fifth layer. Layers represent processing stages; enforcement points represent constraints on transitions. The distinction matters — conflating them inflates the stack and obscures ownership.

In regulated contexts (banking, healthcare), these gates must be synchronous and non-bypassable. In general contexts, the same principle applies at lower stakes: name the gate, name the owner, make it structural rather than conventional.

## Practical Use

- Use as a diagnostic: map any existing AI system to these four layers to find gaps.
- Use as a design anchor: start every new solution by assigning components to layers.
- Use as a communication frame: each layer maps to a different stakeholder concern (product, ML, data, platform).

## What's Not a Layer (but needs to be designed in)

- **Eval/observability** — not runtime, but must be designed in from day one. Retrofitting is painful.
- **Guardrails / human-in-the-loop** — often bolted on; should be a design decision per layer.
