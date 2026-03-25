# Strategos Research: AI Dev Workflow Frameworks 2024–2026

*Researcher output — March 14 2026. Covers agentic coding frameworks, multi-agent workflows, methodology posts, plan-execute patterns, and verification systems. Gaps vs current strategos skill are the primary focus.*

---

## What strategos already does well (skip these)

Cross-referencing against the current skill before listing findings. These are covered and should NOT be re-implemented:

- Solutions KB check (cerno) before planning
- TDD-first task decomposition via CE plan
- Spec analysis for gaps (spec-flow-analyzer)
- Parallel worktree isolation (lucus)
- Tool routing by signal (Codex/Gemini/OpenCode)
- Multi-stage review pipeline (pattern-recognition, kieran-reviewer, security-sentinel, simplicity)
- Verification gate with hard evidence requirement
- Branch cleanup + companion skill creation
- Phase Contract pattern for sequential dependent tasks
- Context packaging checklist for delegates
- Failure mode escalation ladder (lateral tool switch → in-session)

---

## Finding 1: AGENTS.md / Steering Files as a First-Class Artifact

**Source:** [AGENTS.md open standard](https://github.com/agentsmd/agents.md) (Linux Foundation / Agentic AI Foundation, 2025); [Kiro agent hooks](https://kiro.dev/blog/introducing-kiro/); [Windsurf rules hierarchy](https://www.paulmduvall.com/using-windsurf-rules-workflows-and-memories/)

**What it is:** A tiered, repo-specific instruction file that every modern coding agent reads before starting work. Unlike CLAUDE.md (which is operator-level), AGENTS.md is repo-level and project-specific. Kiro extends this with *steering files* (coding standards + preferred workflows) and *hooks* (event-triggered agent actions: e.g., update README when API endpoints change, scan for credential leaks before commit).

**What strategos is missing:** No concept of a generated or validated repo-level agent context file. The CE plan reads the repo, but produces a task plan — not a persistent, delegate-facing spec that future sessions can reuse. Delegates receive context via prompt; this evaporates.

**Worth stealing: YES — high value**

**Concrete suggestion:**
Add a Step 0.5 or a post-planning artifact to strategos: after the CE plan runs, emit a short `AGENTS.md` stub at repo root (or update if one exists). Contents: build commands, test commands, coding conventions discovered, known gotchas from the KB. This file persists across sessions and gives future delegates the same "tribal knowledge" without re-running CE research. Kiro's hook concept is also worth adopting: file-event-triggered agent actions (e.g., on save of `*.py` → lint check, on new API endpoint → update OpenAPI spec). Could be implemented as post-commit hooks that invoke specific CE agents.

---

## Finding 2: Three-File Spec Discipline (requirements / design / tasks)

**Source:** [JetBrains Junie spec-driven approach](https://blog.jetbrains.com/junie/2025/10/how-to-use-a-spec-driven-approach-for-coding-with-ai/); [Addy Osmani's spec guide](https://addyosmani.com/blog/good-spec/); [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD); [Kiro spec format](https://repost.aws/articles/AROjWKtr5RTjy6T2HbFJD_Mw/%F0%9F%91%BB-kiro-agentic-ai-ide-beyond-a-coding-assistant-full-stack-software-development-with-spec-driven-ai)

**What it is:** Practitioners have converged on a three-file spec structure that persists in the repo:
- `requirements.md` — user stories + acceptance criteria (Kiro uses EARS notation)
- `design.md` or `plan.md` — implementation strategy, architecture, data models, API contracts
- `tasks.md` — checkbox list grouped by phase, each linked to a requirement

The key insight is **bidirectionality**: code changes can trigger spec updates, and spec updates regenerate tasks. Kiro enforces this automatically; manual workflows use agent prompts.

**What strategos is missing:** The CE plan + writing-plans output is ephemeral — it lives in `/tmp/`, is consumed by delegates, and disappears. There's no persistent, version-controlled spec artifact that links implementation to requirements. The `HOTFIX_BYPASS.md` pattern shows we value artifact-based accountability, but only for exceptions.

**Worth stealing: YES — medium-high value**

**Concrete suggestion:**
At the PLANNING stage, write the output to `/tmp/<project>-spec/` AND to `~/.claude/specs/<project>/` (or repo `.claude/`) — not just consumed temp files. Structure: `requirements.md` (from spec-flow-analyzer output), `tasks.md` (from writing-plans output, checkboxes). Delegates mark tasks complete; strategos reads completion state at review time. This turns the currently ephemeral planning output into a durable artifact that enables: session recovery, progress visibility, post-mortem review.

---

## Finding 3: BMAD's Role-Typed Agent Pipeline

**Source:** [BMAD Method v6](https://github.com/bmad-code-org/BMAD-METHOD); [BMAD methodology explainer](https://www.theaistack.dev/p/bmad)

**What it is:** BMAD (Breakthrough Method for Agile AI Driven Development) structures dev work as six sequential agent roles: Analyst → PM → Architect → Scrum Master → Developer → QA. Each produces a specific artifact, and the Scrum Master role is particularly notable — it converts architecture docs into "hyper-detailed development stories that embed full context, implementation details, and architectural guidance." The QA agent classifies issues by severity: Blocker / Major / Minor. v6 adds 19 specialized agents and 50+ workflow templates.

**What strategos is missing:** The Analyst and PM roles (pre-spec phases). Strategos starts at planning assuming requirements are already clear. The BMAD Analyst role does structured brainstorming (goals / constraints / risks / open questions / next steps) before any PRD work begins. The PM role then generates formal acceptance criteria. Strategos routes to `/workflows:brainstorm` for unclear requirements, but this is a manual escape hatch — not a gated phase.

Also: severity classification in the review phase. Strategos reviewers surface issues but don't triage them. A Blocker vs Minor distinction would change the review → finish routing.

**Worth stealing: PARTIAL**

- The Analyst phase for ambiguous requirements: worth adding as a lightweight gate before spec-flow-analyzer. If requirements feel thin, run a structured brainstorm that explicitly produces: goals, constraints, risks, open questions. Not a full BMAD session — just the checklist.
- Severity classification in review: YES. Pattern-recognition and kieran-reviewer agents should output findings tagged `[blocker]` / `[major]` / `[minor]`. Blockers = must fix before finish; majors = fix or document; minors = optional.

**Concrete suggestion:**
Add to Step 0 (pre-flight): quick ambiguity check. If requirements are vague, invoke a structured 5-minute analyst pass before spec-flow-analyzer — output: one-line goal, top 3 constraints, top 2 risks, any open questions that need human input before proceeding.
Add to Step 4 (review): require reviewers to classify findings by severity. Add merge policy: `[blocker]` findings block finish; `[major]` findings require documented decision (fix or accept-risk); `[minor]` findings are optional.

---

## Finding 4: Anthropic's Two-Agent Initializer/Coding Pattern

**Source:** [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

**What it is:** Anthropic's own research on long-running coding agents distinguishes two distinct agent modes:
1. **Initializer agent** (runs once): sets up infrastructure, creates the feature list with 200+ items, initializes git, writes `claude-progress.txt`
2. **Coding agent** (runs repeatedly): reads progress + git history at session start, works on ONE feature, makes a clean commit, leaves the environment production-ready

The coding agent is constrained to only mark a `"passes"` boolean on the feature list — it cannot modify or delete items. Session startup ritual: `pwd`, read progress log, read git history, run E2E tests on existing functionality, THEN start new work.

**What strategos is missing:** The mandatory session startup ritual for long-running / multi-session projects. When strategos resumes a task after a session gap, there's no enforced "read the current state before acting" gate. Delegates are given context at prompt-writing time, but if they're re-invoked in a new session, they start fresh. The feature-list + progress-file pattern is a lightweight coordination protocol that prevents "re-doing work that's already done."

**Worth stealing: YES — for multi-session projects**

**Concrete suggestion:**
For any project spanning >1 session, add a `claude-progress.txt` convention to the PLANNING output: a running log (append-only) of what each session completed, what failed, and what the next session should start with. The spec file becomes the source of truth; progress.txt is the execution log. Delegates receive both. Post-execution, strategos appends the summary to progress.txt before closing. This costs almost nothing to add and solves the "session amnesia" problem for multi-day builds.

---

## Finding 5: Kiro's Event-Driven Hooks (Automation Triggers)

**Source:** [Kiro introduction blog](https://kiro.dev/blog/introducing-kiro/); [AWS Kiro DevOps agents](https://devops.com/aws-adds-specialized-ai-agents-to-kiro-coding-tool-to-automate-devops-tasks/)

**What it is:** Kiro introduces "hooks" — event-triggered agent actions that fire on file system events, not on user prompts. Examples: saving a React component triggers a test file update; creating a new API endpoint triggers README and OpenAPI spec refresh; pre-commit triggers credential leak scan. These are declared in YAML and run without human initiation.

**What strategos is missing:** Post-execution automation. After a delegate ships code, strategos validates and reviews — but the validation is always manually triggered by the orchestrator reading output. The hooks concept suggests a pattern where certain post-execution checks fire automatically based on what was changed (detected from git diff).

**Worth stealing: PARTIAL — inspiration more than direct adoption**

**Concrete suggestion:**
Add a post-delegation hook table to strategos. Based on what `git diff --stat` shows was changed, auto-trigger the appropriate review agents:
- `*.py` changes → kieran-python-reviewer (already exists, just make it automatic)
- `*.rs` changes → kieran-rust-reviewer
- Files matching `*auth*`, `*secret*`, `*key*`, `*token*` → security-sentinel always
- `*api*`, `*endpoint*`, `*route*` → docs update check

This converts the current "run review agents in this order" to "run the right review agents based on what changed."

---

## Finding 6: Codified Context — Tiered Knowledge Architecture

**Source:** [Codified Context paper, arxiv:2602.20478](https://arxiv.org/html/2602.20478v1)

**What it is:** A real-world system built over 283 sessions on a 108K-line C# codebase. Three-tier knowledge architecture:
- **Tier 1 (hot, always loaded):** ~660-line Markdown "constitution" — standards, naming, architectural patterns, task routing tables
- **Tier 2 (warm, agent-specific):** 19 specialist agent specs (~9,300 lines total), each with >50% domain knowledge embedded (not just behavioral instructions)
- **Tier 3 (cold, on-demand):** 34 subsystem spec docs (~16,250 lines) retrieved via MCP when a task touches that subsystem

The key insight: **automatic task routing via trigger tables** — maps file modifications to the appropriate specialist agent. Also: "intentional knowledge overlap" — agents embed relevant specs locally rather than relying solely on retrieval, because retrieval brevity bias was causing agents to under-use domain knowledge.

**What strategos is missing:** The trigger-table routing concept (file mod → agent assignment) is the most novel element. Strategos routes by tool (Codex/Gemini/OpenCode) and task signal, but not by which *review specialist* should fire based on what files changed. The Tier 3 on-demand retrieval is also more sophisticated than our current solutions KB check — it's continuous, not just pre-flight.

**Worth stealing: YES — the trigger table and tiered context concepts**

**Concrete suggestion:**
Build a file-type-to-review-agent routing table into strategos (see Finding 5). Also: for complex, long-running projects, the Codified Context three-tier model is worth building out as a project scaffold: constitution.md (always) + domain-agent specs (warm) + subsystem docs (cold / cerno). This is a project-level enhancement, not a strategos change.

---

## Finding 7: The Document-and-Clear Context Reset Pattern

**Source:** [Shrivu Shankar's Claude Code workflow](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)

**What it is:** For complex multi-phase tasks, the orchestrator dumps all progress into a markdown artifact, clears the session context, then restarts by reading that artifact. This creates "durable external memory without relying on opaque auto-compaction." The author also notes a key baseline: a fresh monorepo session consumes ~20% of the 200k context window before any work begins, leaving 80% for actual work — useful for planning context budgets.

**What strategos is missing:** An explicit context reset trigger. Long strategos sessions (planning → multiple delegate cycles → review → review follow-ups) can accumulate significant context noise. Currently, this is handled by manual `/clear` or `/compact`, but there's no built-in trigger based on context usage.

**Worth stealing: YES — lightweight**

**Concrete suggestion:**
Add to the strategos scope checkpoint (Step 1.5): "If this session has been running >90 min or context is >60% full, suggest document-and-clear: dump current state to `/tmp/<project>-handoff.md` and restart with that file as the only context." This is a one-sentence addition that prevents late-session degradation on long builds.

---

## Finding 8: Armin Ronacher's Toolability Principles

**Source:** [Armin Ronacher — Agentic Coding Recommendations](https://lucumr.pocoo.org/2025/6/12/agentic-coding/)

**What it is:** Ronacher (Flask/Jinja/Ruff creator) shares practitioner-level insights on what makes a codebase agent-friendly:
- Tools must be **fast** (slow compilation = expensive agent loops), **clear** (explicit errors guide agents forward), **robust** (no undefined behavior), **observable** (logs to files, not stdout)
- Agents produce better SQL than ORM queries — prefer plain SQL
- Avoid "magic" (pytest fixtures, metaclasses) — agents find explicit code easier
- Favor "functions with clear, descriptive, longer-than-usual names over classes"
- Avoid inheritance; write "the dumbest possible thing that will work"
- Speed dominates cost: optimize tool execution time over token efficiency
- Refactor proactively — extract components before complexity exceeds what agents can manage; 50+ file scattering = agent performance cliff

**What strategos is missing:** A codebase readiness gate. Before delegating to agents, strategos doesn't check whether the target codebase is agent-friendly (observable, explicit, no magic). This is particularly relevant for Capco consulting work where the codebase may be client-owned and opaque.

**Worth stealing: YES — as a pre-delegation checklist item**

**Concrete suggestion:**
Add to Step 0 (pre-flight), for existing codebases: quick agent-readiness check. Three questions: (1) Does the build/test command run in <30s? If not, delegates will burn tokens on slow loops. (2) Does the project have magic (heavy DI, metaclasses, ORM magic)? Flag it — delegates may hallucinate around it. (3) Are errors explicit (not swallowed exceptions)? If not, add a note to the delegate prompt to add logging first. These three checks take 2 minutes and can save hours.

---

## Finding 9: Severity-Gated Review + PR Evidence Standard

**Source:** [Simon Willison — Agentic engineering anti-patterns](https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/); multi-agent adversarial testing frameworks

**What it is:** Willison's core anti-pattern: filing PRs with unreviewed agent-generated code, with no evidence of personal review. His standard: PRs must include notes on how the code was manually tested, comments on implementation choices, screenshots or video evidence. The adversarial testing research introduces Red-Blue team dynamics: Red agents generate attacks/edge cases, Blue agents patch and reinforce.

**What strategos is missing:** The PR evidence standard is partially covered (verification gate requires pasted output), but there's no formal "evidence package" structure for the PR itself. The Red-Blue adversarial pattern is entirely absent — our multi-agent review is collaborative (all reviewers try to improve), not adversarial (one tries to break what the other built).

**Worth stealing: PARTIAL**

- PR evidence package: add to Step 4.6 (Finish). The PR description should include: what was manually tested, at least one non-trivial test output pasted, any implementation choices that differed from the plan and why.
- Red-Blue review: interesting but heavyweight. Simpler version: ask one review agent to "find the three most likely ways this will fail in production" rather than just "review for quality." Adversarial framing elicits different findings than collaborative framing.

**Concrete suggestion:**
Add a "fail-this" pass to the review pipeline: after kieran-reviewer runs collaboratively, invoke a separate subagent with: "You are adversarial. Assume this code will be deployed to production next week. Find the three most likely failure modes, data edge cases, or security issues that escaped review. Be specific." This adversarial framing consistently surfaces issues that collaborative review misses.

---

## Finding 10: Self-Improving Loop (GHA Flywheel)

**Source:** [Shrivu Shankar's Claude Code workflow](https://blog.sshh.io/p/how-i-use-every-claude-code-feature); [SSI-FM self-improving coding agent, ICLR 2025](https://openreview.net/forum?id=rShJCyLsOr)

**What it is:** A GitHub Actions pipeline that creates an auditable self-improvement loop: agent execution logs → analysis of failure patterns → CLAUDE.md / strategos improvements → better agent performance. The SSI-FM paper formalizes this as reflection + self-revision on programming tasks. Karpathy's autoresearch (March 2026) is the cleanest version: agent edits script → runs time-boxed experiment → measures → keep/discard → repeat.

**What strategos is missing:** The `/workflows:compound` step at the end is the existing learning capture mechanism — it writes to `~/docs/solutions/`. But compound is manually triggered and requires user prompting. There's no automatic failure pattern analysis across sessions.

**Worth stealing: YES — for the long run, not an immediate change**

**Concrete suggestion:**
This is a future enhancement, not a strategos patch. Immediate action: make compound mandatory (not optional) after any non-trivial build. Medium-term: build a lightweight log aggregator that reads `~/.cache/plan-exec/` outputs weekly and surfaces recurring delegate failure patterns to strategos for rule updates. This is what `/weekly` should eventually include.

---

## Summary: Priority Ranking for Strategos Incorporation

| # | Finding | Effort | Value | Verdict |
|---|---------|--------|-------|---------|
| 1 | Severity-gated review (Blocker/Major/Minor) | Low | High | Ship next |
| 2 | Adversarial "fail-this" review pass | Low | High | Ship next |
| 3 | Document-and-clear context reset trigger | Low | Medium | Ship next |
| 4 | File-type → review agent routing table | Medium | High | Next session |
| 5 | AGENTS.md generation at planning stage | Medium | High | Next session |
| 6 | PR evidence package standard (Step 4.6) | Low | Medium | Next session |
| 7 | claude-progress.txt for multi-session projects | Medium | Medium | Next session |
| 8 | Agent-readiness pre-flight check (Step 0) | Low | Medium | Next session |
| 9 | Three-file spec persistence (req/design/tasks) | High | High | Consider for new project scaffold |
| 10 | Analyst ambiguity gate (pre-planning) | Medium | Medium | Optional, already handled by brainstorm routing |
| 11 | Self-improving GHA flywheel | High | High | Future |

---

## What's NOT worth stealing

- **Full BMAD pipeline**: The 6-role sequential agent model adds overhead for the Analyst/PM/Architect phases that strategos already handles or bypasses consciously. The Scrum Master "hyper-detailed story" concept is what writing-plans already does.
- **LangGraph / AutoGen / framework-level orchestration**: Strategos orchestrates via shell + lucus worktrees, not a graph framework. Adding a graph framework would be architecture change, not a workflow improvement.
- **EARS notation for acceptance criteria**: Useful in large team settings; overkill for personal/small-team use. The added formalism doesn't improve delegate performance enough to justify the extra spec-writing overhead.
- **Full Codified Context three-tier system**: Correct for 108K-line codebases over 283 sessions. Disproportionate for most of our projects. Adopt selectively (trigger tables, tiered context) not wholesale.

---

## Sources

1. [AGENTS.md open standard — Linux Foundation/AAF](https://github.com/agentsmd/agents.md)
2. [Kiro: Spec-Driven AI Coding (AWS)](https://kiro.dev/blog/introducing-kiro/)
3. [BMAD Method v6](https://github.com/bmad-code-org/BMAD-METHOD)
4. [BMAD 6-Step explainer — The AI Stack](https://www.theaistack.dev/p/bmad)
5. [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
6. [Codified Context: Infrastructure for AI Agents in Complex Codebases — arxiv:2602.20478](https://arxiv.org/html/2602.20478v1)
7. [Addy Osmani: How to write a good spec for AI agents](https://addyosmani.com/blog/good-spec/)
8. [JetBrains Junie: Spec-driven approach](https://blog.jetbrains.com/junie/2025/10/how-to-use-a-spec-driven-approach-for-coding-with-ai/)
9. [Windsurf Rules, Workflows, Memories — Paul Duvall](https://www.paulmduvall.com/using-windsurf-rules-workflows-and-memories/)
10. [Armin Ronacher: Agentic Coding Recommendations](https://lucumr.pocoo.org/2025/6/12/agentic-coding/)
11. [Simon Willison: Agentic engineering anti-patterns](https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/)
12. [Shrivu Shankar: How I use every Claude Code feature](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)
13. [AI Checkpointing methodology — HAMY](https://hamy.xyz/blog/2025-07_ai-checkpointing)
14. [Nxcode: Agentic Engineering complete guide 2026](https://www.nxcode.io/resources/news/agentic-engineering-complete-guide-vibe-coding-ai-agents-2026)
15. [Teamday: Complete guide to agentic coding 2026](https://www.teamday.ai/blog/complete-guide-agentic-coding-2026)
16. [ByteByteGo: Top AI agentic workflow patterns](https://blog.bytebytego.com/p/top-ai-agentic-workflow-patterns)
17. [SSI-FM: Self-improving coding agent — ICLR 2025](https://openreview.net/forum?id=rShJCyLsOr)
18. [AI Agentic Programming Survey — arxiv:2508.11126](https://arxiv.org/html/2508.11126v1)
19. [barkain Claude Code workflow orchestration plugin](https://github.com/barkain/claude-code-workflow-orchestration)
20. [Anthropic 2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)
