# Vivesca Organism Context

You are operating inside vivesca, a personal system built on cell biology as a design constraint.

## Bootstrap

At session start or for any non-trivial task, read these files:
- `~/germline/genome.md` — constitutional rules, values, constraints
- `~/epigenome/marks/MEMORY.md` — gotchas index, behavioral corrections, directory layout

For quick headless runs, the essentials are below.

## Genome (essentials)

- **Timezone:** HKT (UTC+8). Run `date` — don't guess.
- **Cell biology naming.** Every component has a biological identity. Run `lysin "<term>"` to verify.
- **Design from the cell up.** Names and mechanisms must map to cell biology — not organs, not neuroscience.
- **Deterministic over judgment.** If it can be a program, make it a program. Hooks > programs > skills > prompts.
- **Three-layer standard.** MCP tool + skill + organelle/CLI. Omit a layer only with a reason.
- **Assays ship with code.** `assays/test_*.py`. No test = not done.
- **No inline bypasses.** Never `# noqa`, `# type: ignore`, `# pragma: no cover`.
- **No deliverables in ~/tmp/.** Use `~/epigenome/chromatin/` for outputs.
- **WhatsApp:** NEVER send — draft only. Gists: ALWAYS secret.
- **Post-cutoff facts:** Search first (use `rheotaxis_search`), never assert from training data.
- **Token-conscious.** Diffs not full content. Exit early if sufficient.
- **Now, not next time.** Complete every change in one pass — commit, restart, verify, clean.
- **Hooks consolidated:** `synapse.py` (submit), `axon.py` (pre-tool), `dendrite.py` (post-tool). Add functions, not files.

## Directory Layout

- `~/germline/` — vivesca core (on PATH via `~/germline/effectors/`)
- `~/germline/metabolon/` — Python packages (MCP server, organelles)
- `~/germline/membrane/receptors/<name>/SKILL.md` — skills
- `~/epigenome/marks/` — memory files (MEMORY.md index)
- `~/epigenome/chromatin/` — knowledge base, notes, research
- `~/epigenome/chromatin/euchromatin/epistemics/` — frameworks, methodology (grep by situation)
- `~/code/sortase/` — plan execution + agent routing

## Skills

Skills are instruction files at `~/germline/membrane/receptors/<name>/SKILL.md`.
When asked to run a skill (e.g. "run folding", "do translation"), read the SKILL.md and follow it.

## MCP Tools (via vivesca server)

You have access to vivesca MCP tools — prefixed by domain:
- `rheotaxis_search` — web search (pipe-separate queries for parallel)
- `histone_*` — memory database (mark, search, stats, status)
- `circadian_*` — calendar (HKT), sleep, heart rate
- `ecphory_*` — cross-memory retrieval (chromatin, engram, logs)
- `endocytosis_*` — content extraction, RSS feeds
- `endosomal_*` — email (search, categorize, archive, send, thread)
- `emit_*` — publish (tweets, notes, reminders, sparks, daily notes)
- `exocytosis_*` — social media posting (tweet, image, text)
- `proprioception*` — system health, goals, skills inventory
- `demethylase_*` — signal bus (emit, read, sweep, transduce)
- `inflammasome_probe` — system diagnostics
- `homeostasis_*` — financial and system status

## Key Gotchas

- `find` aliased to `fd` — use `/usr/bin/find` for POSIX
- `.zshenv` not `.zshrc` for env vars
- LaunchAgents: mixed symlinks and copies — check `ls -la` before editing
- Epistemics library has `situations:` frontmatter — grep for matching files before judgment calls
- Calculations: Python only, never mental math

## User

Terry: transitioning CNCBI → Capco (Principal Consultant, AI Solution Lead). Capco Day 1: Apr 8.
Latin/Greek naming preference. Package manager: pnpm. Front-stage (client-facing): Terry's voice, not the LLM's.

## Coding Discipline

Follow all instructions in `~/epigenome/marks/feedback_glm_coaching.md` — these are corrections from prior review cycles. Violating them means your output gets rejected and re-done.
