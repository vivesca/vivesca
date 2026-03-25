---
module: AI Agent Orchestration
date: 2026-03-06
problem_type: best_practice
component: mental_model
tags: [agent, autonomous, monitoring, long-running, correctness-signal, karpathy]
related_files:
  - /Users/terry/docs/solutions/ai-tooling/karpathy-agent-research-org.md
  - /Users/terry/skills/heuretes/SKILL.md
---

# Autonomous vs Monitored Agents — Correctness Signal Principle

## Insight

The question "should this agent run autonomously or be monitored?" is often framed as a trust/maturity question. The better frame is: **how fast and cheap is the correctness signal?**

> Automate where you can verify cheaply. Monitor where you can't.

## Source

Karpathy's nanochat agent research org (Mar 2026). He runs long-running agents but keeps a tmux grid open — not because he distrusts agents, but because research tasks have no fast automated eval. His perf improvement loop (does validation loss go down?) runs unattended. His research org (are these experiment ideas any good?) he watches.

## The Framework

| Correctness signal | Agent mode | Rationale |
|---|---|---|
| Automated, fast (test pass, metric threshold, lint) | Autonomous — fire and forget | Wrong answers surface immediately, cost of failure is low |
| Human judgment, delayed | Monitored — periodic check-ins | You need to catch wrong turns before they compound |
| Undefined / emergent | Human-led short sessions | No way to evaluate without being present |

## Implications for Our Setup

- **nanochat-style perf loops** (run experiment, check metric, merge if better): full autonomy fine
- **Research/comparison tasks** (heuretes): launch background Tasks, read findings.md as they land, stop bad tracks early
- **Architecture decisions, creative work**: keep human in the loop from the start

The "long-running agents" trend is real but applies cleanly only to the first row. Most knowledge work sits in the second row — long-running but needing periodic human review, not true autonomy.

## Why This Matters

Getting the mode wrong in either direction is costly:
- Too autonomous on judgment-heavy tasks: agents run confidently in the wrong direction for hours
- Too monitored on verifiable tasks: you're babysitting work that could run fine unattended

The correctness-signal frame resolves this without relying on vague intuitions about agent "trustworthiness."
