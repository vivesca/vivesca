---
name: modification
description: Refine an artifact via multi-model iteration or solo cooling. "refine", "polish", "anneal"
aliases: [refine, polish]
user_invocable: true
runtime: skill
context: fork
epistemics: [evaluate, build]
---

# Litura

Multi-model iterative refinement. From Latin *modification* — the visible mark of revision.

Multiple LLM models independently review an artifact, cross-judge each other, synthesize consensus, and iterate until convergence. Uses CC native agent teams for orchestration and Gemini/Codex/OpenCode CLIs as independent external reviewers.

---

## When to Use

- An artifact needs quality beyond single-model capability
- Multiple perspectives would catch different issues (e.g., CV: content, formatting, audience fit)
- You want adversarial review (one model attacks, another defends)
- Quality matters enough to justify 3-5 minutes and cross-model token spend

## When NOT to Use

- Simple edits with clear requirements — just do them
- Factual research — use rheotaxis or web search
- Decisions/trade-offs — use quorum
- Time-critical with no room for iteration
- Single-model cooling when multi-model is overkill — use solo mode (below)

---

## Solo Mode (single-model cooling)

For artifacts that need refinement but don't warrant multi-model overhead. Absorbed from annealing.

**When:** doc/spec exists but is bloated, a draft needs compression, or post-brainstorm convergence. One model, four passes.

### Cooling schedule

1. **HOT** — Rewrite from memory with zero fidelity constraint. Surface what the careful draft suppressed.
2. **WARM** — Compare hot draft to original. Extract the best of each. Cut anything in neither.
3. **COOL** — Every sentence must earn its place. Target 40-60% of warm draft word count.
4. **COLD** — Read aloud (simulate). Flag anything that sounds wrong, any gap a reader stumbles on. Ship.

**Anti-patterns:** Skipping HOT (loses the honest layer). Re-heating after COLD (return to WARM instead). One mega-pass (quenching, not annealing — produces brittle output).

---

## Pre-flight

Before spawning reviewers:
- **Artifact exists and is readable?** Check path. Common failure: stale path from earlier session.
- **External models available?** Quick check: `gemini --version` and `codex --version`. If a backend is down, adjust team composition rather than failing mid-review.
- **Rubric specified?** If not, ask. "Refine this" without criteria produces generic feedback. Even "make it better for [audience]" is enough to anchor review.

## Inputs

1. **Artifact** — file path to the thing being refined
2. **Rubric** — what "good" looks like (criteria + weights). Can be inline or a file.
3. **Context** — who's the audience, what's the purpose, any constraints

---

## Process

### Step 1: Set up the team

```
TeamCreate: modification-<artifact-name>
```

Create tasks with dependencies:
1. Independent review (parallel)
2. Synthesize consensus (blocked by #1)
3. Apply edits (blocked by #2)
4. Validation round (blocked by #3)
5. Present result (blocked by #4)

### Step 2: Parallel independent review

Spawn 3-4 reviewers in parallel. Mix of internal (Claude agents) and external (Gemini/Codex/OpenCode via Bash).

**Model routing (token-conscious):**
- Gemini CLI: `gemini -m gemini-3.1-pro-preview -p "<prompt referencing file in workspace>"`
  - Sandbox constraint: can only access workspace dir. Place artifacts within workspace or reference existing paths.
- Codex CLI: `/opt/homebrew/bin/codex exec --ephemeral --skip-git-repo-check "<prompt referencing file path>"`
  - Read-only sandbox. Reviews are inline in output, not written to file. Capture output.
- OpenCode CLI: `opencode run "<prompt>"` (uses configured model)
- Claude agents: via Agent tool with `team_name` parameter

**Key rules:**
- Don't assign role personas (strategist, red-team, etc.) — diversity comes from different models, not different prompts
- Each reviewer gets the same rubric and context
- Each writes output to a chromatin or docs path — **never ~/tmp/**
- Each scores 1-10 on each rubric criterion

### Step 3: Synthesize consensus

Launch a synthesizer agent (Claude, on the team) that:
1. Reads all review outputs
2. Identifies: unanimous agreement (implement), majority agreement (likely), disagreements (flag)
3. Ranks changes by how many reviewers flagged them
4. Writes consensus doc to chromatin

**Tell research agents to SendMessage findings directly to the synthesizer** — fan-in pattern.

### Step 4: Apply edits

Synthesizer (or a new agent) applies consensus edits to the artifact. Regenerates any derived outputs (PDFs, etc.).

### Step 5: Validation round

Run Gemini + Codex (cheapest independent models) on the revised artifact with the same rubric.

**Convergence criterion:** All models score 8+ on all criteria → done. If not → back to Step 2 with the delta only (not full artifact).

**Hard cap:** 3 rounds max. Diminishing returns after that.

### Step 6: Present and clean up

- Show the user: final diff, scores, and artifact location
- Shut down teammates via SendMessage shutdown_request
- TeamDelete to clean up

---

## Token Efficiency Rules

1. **Route cheap.** Gemini/Codex/OpenCode for review rounds (free or near-free). Claude only for synthesis/judgment.
2. **Send diffs after round 1.** Models see only the delta + rubric, not the whole artifact.
3. **Exit early.** If round 1 scores 8+ across all models, stop. Don't iterate for iteration's sake.
4. **Hard cap: 3 rounds.** If not converged after 3, present what you have with remaining issues flagged.
5. **Every token not spent here is a token lucerna can use.**

---

## Parallel Research Pattern

If the artifact needs context (e.g., CV needs company research), spawn research agents alongside reviewers:

```
reviewer-1 (Gemini) ──┐
reviewer-2 (Codex)  ──┤
reviewer-3 (Claude) ──┼──→ synthesizer ──→ revised artifact
researcher-1        ──┤
researcher-2        ──┘
```

Research agents SendMessage findings to the synthesizer for incorporation. Shut down after delivering.

---

## Rubric Template

```markdown
## Rubric: [Artifact Name]

**Audience:** [who reads this]
**Purpose:** [what it needs to achieve]

| Criterion | Weight | What 8+ looks like |
|-----------|--------|-------------------|
| [e.g., Relevance to role] | High | [description] |
| [e.g., Clarity] | Medium | [description] |
| [e.g., No buzzwords] | Low | [description] |
```

---

## Authority Hierarchy

When rubric criteria conflict with the artifact's existing style or context:

1. **Existing design system / voice / conventions** — match what's established
2. **User's explicit rubric** — override defaults, not existing identity
3. **Reviewer defaults** — apply only in the absence of context

Don't "improve" a casual blog post into formal prose, or impose Anthropic style on a personal essay. The artifact's identity takes precedence over generic quality heuristics.

## Gotchas (sharp edges first)

- **Gemini sandbox:** Only accesses its workspace dir. Reference files within workspace, never ~/tmp/. This is the #1 cause of "reviewer returned empty" — check paths.
- **Codex read-only:** Can't write files. Review output is inline — capture from task output.
- **Don't role-assign Claude agents.** "Strategist", "red team", "hiring manager" — overkill. Different models provide diversity, not different prompts.
- **Deliverables never in ~/tmp/.** Tell agents to write to chromatin or ~/germline/loci/.
- **Don't narrate play-by-play to the user.** Set up the team, let it run, present the final result.

---

## See Also

- quorum — for decisions/judgment (deliberation, not refinement)
- polarization — for overnight autonomous work (different pattern)
