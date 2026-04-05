---
name: scrutor
description: Code audit using Codex, OpenCode, or consilium. Use when reviewing code for bugs, security issues, or logic errors.
user_invocable: true
triggers:
  - scrutor
  - audit
  - code review
  - security audit
---

# Scrutor

Code review via delegated LLMs. Routes by scope and severity.

## Routing

| Use case | Tool |
|---------|------|
| Single file, general bugs | Codex (GPT-5.2) — primary, 92% signal |
| Secondary pass / edge cases | OpenCode (GLM-4.7) — two-phase prompt, 25% signal |
| Security / compound vulns | Consilium red team — catches attack chains |
| Important code | All three in parallel, triage by consensus |

## Codex — primary auditor

92% signal rate (11/12 real bugs on rai.py). Use for all audits.

```bash
codex exec --skip-git-repo-check --full-auto \
  "Perform a thorough code audit of <file>. Focus on: bugs, data integrity, edge cases, error handling, security, race conditions, logic errors. For each finding: severity (HIGH/MED/LOW), line numbers, the bug, suggested fix."
```

Triage: Codex finds real bugs but also suggests over-engineering. Ask "would I notice this during actual use?" to filter.

## OpenCode (GLM-4.7) — secondary

**Naive prompt → 0% signal** (25 false positives). GLM pattern-matches vulnerability templates without verifying.

**Two-phase prompt → 25% signal** (1/4 real, found a bug Codex missed):

```bash
opencode run --model opencode/glm-4.7 \
  "Phase 1: Read <file> thoroughly. This is a <context — personal CLI / server / library>. List all potential bugs, but DO NOT report yet.

Phase 2: For EACH potential finding, re-read the specific lines to verify:
- Does the bug actually exist in the current code?
- Is there already a guard/check that handles it?
- Is it relevant for <context>?

Only report findings that survive verification. For each: severity, exact line numbers, the actual buggy code (quote it), why it's real, suggested fix. Drop anything that doesn't survive Phase 2."
```

## Consilium red team

Best for **security audits and compound vulnerability discovery**. 5 frontier models attack the code simultaneously, then a judge triages. Catches attack chains that single-model review misses (e.g., SSRF → log injection → prompt injection → LLM exfiltration). ~$1.50/run.

```bash
# Bundle source files with headers
for f in src/**/*.py; do echo "## $f"; echo '```python'; cat "$f"; echo '```'; echo; done > /tmp/review.md

# Run red team with actual code
PROMPT=$(cat /tmp/review.md)
uv tool run consilium "$PROMPT" --redteam --output ~/epigenome/chromatin/Councils/review.md
```

**Key:** Models can't read files — paste actual code into the prompt. ~55K chars (8 modules) works fine. Use for whole-codebase security review, not single-file bugs.

## After audit: parallel fixes

Launch one OpenCode per fix in parallel. Keep prompts to "read this range, change X to Y, run tests". OpenCode handles simple substitutions; complex structural transforms silently stall — do those directly.

## Calls
- `mitogen` — for dispatching parallel fixes
- `consilium` — for red team reviews

## Motifs
- [audit-first](../motifs/audit-first.md)
- [escalation-chain](../motifs/escalation-chain.md)
