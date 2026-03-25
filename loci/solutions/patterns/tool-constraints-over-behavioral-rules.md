# Tool Constraints > Behavioral Rules (for AI Agents)

> Source: LLM Council deliberation on memory system improvements (2026-02-19)

## The Pattern

When you need an AI agent to follow a specific workflow (e.g., "search vault before searching conversation memory"), **tool-level wrappers are the only trustworthy enforcement.** CLAUDE.md instructions are soft guidance — the model can and will skip them under pressure, distraction, or context truncation.

## Why Behavioral Rules Fail

- CLAUDE.md rules compete with hundreds of other instructions for attention
- Under context pressure (long conversations, compaction), nuanced rules get dropped first
- The model has no mechanism to verify it followed the rule — it just proceeds
- "Always do X before Y" collapses to "do X or Y, whichever seems relevant"

## Why Tool Wrappers Work

A wrapper like `cerno` (which searches QMD first, falls back to Oghma) enforces the waterfall at the tool level. The agent calls ONE command and the ordering is guaranteed. No instruction-following required.

## Decision Rule

| Enforcement need | Mechanism |
|-----------------|-----------|
| **Nice to have** | CLAUDE.md instruction |
| **Should happen** | CLAUDE.md + MEMORY.md reminder |
| **Must happen** | Tool wrapper / hook / script |

If the enforcement mechanism is "the skill instructions tell Claude to do it," **stress-test it first.** If it collapses to one prompt line, it was always one prompt line — skip the infrastructure and just write the wrapper.

## Examples

- **Search order** → `cerno` wrapper enforces QMD-first waterfall
- **No rm -rf** → `bash-guard.js` hook blocks the command
- **Format on save** → PostToolUse hook runs prettier/ruff automatically
- **Dedup before write** → MEMORY.md reminder (acceptable — low-stakes, behavioral nudge is proportionate)

## Anti-Pattern

Building elaborate "memory" or "learning" systems where the only enforcement is prompt instructions. If you need it to stick, put it in the tool, not the prompt.
