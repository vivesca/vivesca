---
module: AI Agent Orchestration
date: 2026-03-06
problem_type: best_practice
component: workflow
tags: [agent-org, research, karpathy, multi-agent, delegation, orchestration, git-worktrees]
source: https://x.com/karpathy (tweets Feb-Mar 2026)
related_files:
  - /Users/terry/skills/heuretes/SKILL.md
  - /Users/terry/skills/rector/SKILL.md
  - /Users/terry/skills/lucus/SKILL.md
---

# Karpathy's Agent Research Org Pattern

## Context

Andrej Karpathy independently arrived at a multi-agent orchestration architecture (via his nanochat project, Mar 2026) that strongly converges with our compound engineering + superpowers setup. Not an endorsement — **independent convergence** from a highly credible practitioner. Useful as validation and vocabulary.

## Key Quotes

**On "programming an org":**
> "The goal is that you are now programming an organization (e.g. a 'research org') and its individual agents, so the 'source code' is the collection of prompts, skills, tools, and processes that make it up. E.g. a daily standup in the morning is now part of the 'org code'."

**On the new meta-benchmark:**
> "What is the research org agent code that produces improvements on nanochat the fastest? — this is the new meta."

**On how much programming has changed (Feb 2026):**
> "You're not typing computer code into an editor like the way things were since computers were invented, that era is over. You're spinning up AI agents, giving them tasks in English and managing and reviewing their work in parallel."

**On the 80/20 exploration heuristic:**
> "The art of the process is spending 80% of the time getting work done in the setup you're comfortable with and that actually works, and 20% exploration of what might be the next step up even if it doesn't work yet. If you're too conservative, you're leaving leverage on the table. If you're too aggressive, you're net creating more chaos than doing useful work."

**On agent quality limits:**
> "The agents' ideas are just pretty bad out of the box, even at highest intelligence. They don't think carefully through experiment design, they run non-sensical variations, they don't create strong baselines and ablate things properly, they don't carefully control for runtime or flops. They are very good at implementing any given well-scoped and described idea but they don't creatively generate them."

**On agent org setup:**
> "8 agents (4 claude, 4 codex), with 1 GPU each... git worktrees for isolation, simple files for comms, skip Docker/VMs for simplicity. Research org runs in tmux window grids of interactive sessions (like Teams) so that it's pretty to look at, see their individual work, and 'take over' if needed."

## Key Insights (distilled)

### 1. Prompts + skills + tools = org source code
The entire agent workflow — prompts, skills, tools, routines, communication patterns — IS the software. Optimising your agent setup is software development. This maps exactly to our hooks + skills + CLAUDE.md architecture.

### 2. The meta-benchmark mindset
Stop asking "did the task complete?" Ask: "which agent org configuration produces the most progress per unit time?" This is the right frame for improving our delegation setup.

### 3. Agent org hierarchy
- **Chief orchestrator** — decomposes task, assigns to juniors, reviews output, merges wins
- **Junior agents** — isolated per git worktree, work on feature branches, report via files
- No Docker/VMs needed — instructions alone prevent interference

### 4. Research fails where implementation succeeds
Agents excel at well-scoped implementation. They fail at open-ended research: experiment design, controls, baselines, ablations. The human's job in a research org is supplying the scientific judgment — not the code.

### 5. 80/20 rule
80% productive work in your current comfortable setup. 20% exploring the next level of delegation. Applied to us: don't always reach for the full CE/parallel-agents stack; reserve it for appropriate tasks and keep 20% capacity for pushing the frontier.

### 6. Daily standup as org code
Routine sync loops (our `/statio`, `/auspex`, `/cardo`) are part of the agent org architecture — not just personal habits.

## What's New vs Our Current Setup

| Karpathy pattern | Our equivalent | Gap |
|---|---|---|
| Chief + junior hierarchy | rector + Task agents | We don't explicitly assign chief/junior roles |
| tmux grid visibility | tmux sessions | We don't monitor parallel agents in a grid |
| Simple files for comms | — | We rely on task output; explicit file handoffs are underused |
| Research org as benchmark | — | We don't measure "agent org efficiency" as a metric |
| 80/20 exploration heuristic | — | Not articulated in any skill |

## Published Work

- nanochat repo: https://github.com/karpathy/nanochat
- No published agent org framework/prompts — all in tweets
- See `heuretes` skill for our implementation of this pattern
