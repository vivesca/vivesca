---
module: AI Agent Orchestration
date: 2026-03-14
problem_type: research
component: workflow
tags: [agent-orchestration, parallel-delegation, multi-agent, dev-workflow, rector]
---

# Agent Orchestration Landscape (Mar 2026)

Research sweep of GitHub agent orchestration repos. Patterns already integrated into rector are marked; the rest are noted for future revisit.

## Repos Worth Revisiting

### Tier 1 — Directly relevant to rector

| Repo | Stars | Key pattern | Status |
|------|-------|-------------|--------|
| [ComposioHQ/agent-orchestrator](https://github.com/ComposioHQ/agent-orchestrator) | ~4.3k | Reaction routing — CI failures auto-route back to owning agent via YAML rules | **Integrated** into rector-reference.md |
| [superset-sh/superset](https://github.com/superset-sh/superset) | ~6.9k | Unified supervision dashboard for 10+ parallel agents (Electron) | Noted — UI layer, not actionable for CLI workflow |
| [generalaction/emdash](https://github.com/generalaction/emdash) | ~2.6k | Provider-agnostic routing (22+ CLI agents), ticket-to-agent from Linear/GitHub/Jira | Revisit when ticket integration matters |
| [automagik-dev/genie](https://github.com/automagik-dev/genie) | ~256 | Severity-gated review block (CRITICAL/HIGH enforced, not advisory), knowledge vault pre-search | Already have severity gating; knowledge vault = cerno |
| [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration) | — | Wave-based dependency analysis, verifier as distinct agent role, file ownership boundaries | **Integrated** (waves + file ownership) into rector-reference.md |
| [workstream-labs/workstreams](https://github.com/workstream-labs/workstreams) | ~25 | Iterative refinement without context restart — review comments re-prompt same agent session | Future build — needs persistent agent sessions |
| [wshobson/agents](https://github.com/wshobson/agents) | — | 72-plugin marketplace, progressive skill disclosure, three-tier model routing | Cherry-picked file ownership pattern; don't install (token budget) |

### Tier 2 — Worth watching

| Repo/Topic | Key idea |
|------------|----------|
| [github.com/topics/agent-orchestration](https://github.com/topics/agent-orchestration) | Umbrella topic — check quarterly |
| [andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) | Curated list — check quarterly |
| [rkoots blog: multi-agent code review](https://rkoots.github.io/blog/2026/03/09/bringing-code-review-to-claude-code/) | Adversarial cross-validation between reviewers — agents debate before surfacing findings |
| GitHub Agentic Workflows (technical preview, Feb 2026) | Markdown-described workflows → GitHub Actions. May subsume some tools within 12 months |
| TAKT (~758 stars) | Declarative human-in-the-loop gates via YAML config |

## Patterns Extracted

### Already integrated into rector (Mar 2026)

1. **File ownership in parallel delegation** — each delegate gets explicit file list, can't touch others
2. **Reaction routing (auto-retry)** — one automatic retry with error context before escalating to human
3. **Wave-based dependency execution** — explicit wave metadata on tasks, parallel within wave, sequential across

### Future ideas (build when pain is felt)

4. **Review-comment-to-agent feedback loop** — re-prompt same agent on same branch with review comments, no cold start. Needs persistent agent sessions (workstreams pattern).
5. **Adversarial cross-validation** — reviewers challenge each other's findings before surfacing to human. Currently we have adversarial pass as a separate prompt; true cross-validation would need inter-agent messaging.
6. **Semantic revert by logical unit** — undo "implement auth" as a unit, not individual commits. Needs tracking metadata across commits (Conductor pattern from wshobson/agents).
7. **Unified supervision dashboard** — one pane showing all agent statuses with attention flags. Currently we use TaskOutput polling. Worth building if parallel delegation becomes daily workflow.

## Meta-observation

The space converged on the same architecture: `git worktree isolation + agent-per-task + CI/review gating + human approval at merge`. Differentiation is in routing intelligence, review gating severity, and autonomy level. Our rector pipeline is competitive with the best of these.
