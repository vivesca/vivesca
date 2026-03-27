---
name: maturation
description: Writing/editing a SKILL.md — quality heuristics for description and structure.
user_invocable: false
---

# maturation -- skill quality heuristics

Design heuristics for writing skills that trigger correctly, load efficiently, and teach clearly.

## Description Field (Most Important)

The description decides whether Claude loads the skill. Get this wrong and nothing else matters.

**Rule: description = when to trigger. Never what the skill does.**

```yaml
# BAD -- summarises capability. Claude may follow this INSTEAD of reading the skill.
description: Query Slack export DB for messages, DMs, threads, and channels

# BAD -- summarises workflow. Claude shortcuts past the actual content.
description: Use when executing plans - dispatches subagent per task with code review

# GOOD -- triggering conditions only. Forces Claude to read the body.
description: Use when reading Slack messages from local export. "check Slack", "Slack DMs"
```

**Why this matters:** Testing showed Claude follows the description as a shortcut. A description saying "code review between tasks" caused ONE review; the skill's flowchart showed TWO. Remove workflow from description, Claude reads the body.

- Start with "Use when..."
- Include symptoms, situations, trigger phrases in quotes
- Third person (injected into system prompt)
- Never summarise the skill's process
- Under 500 characters
- **Lean slightly pushy.** Claude undertriggers -- err toward including edge-case triggers rather than being conservative

**Sanity check:** After writing, think of 3 prompts that SHOULD trigger and 2 that SHOULDN'T. If the description can't distinguish them, rewrite.

## Progressive Disclosure

Skills load in three tiers. Design for this:

1. **Metadata** (name + description) -- always in context. ~100 words. This is your only shot at triggering.
2. **SKILL.md body** -- loaded when skill triggers. Keep under 500 lines.
3. **Bundled references/** -- loaded on demand from body pointers. Unlimited size.

Heavy reference (API docs, schemas >100 lines) goes in `references/`. The body points to it with clear guidance on WHEN to read it. Scripts go in `scripts/` and can execute without loading into context.

## Token Economy

Every skill loaded = tokens burned from context. Budget:

| Frequency | Target |
|-----------|--------|
| Always loaded | <150 words |
| Frequently triggered | <200 words |
| On-demand | <500 words |

**Techniques:** Route to CLI `--help` for flag docs. Cross-reference other skills by name, don't repeat. One example, not five. Compress: 20 words beats 42 for the same point. If agents keep reinventing the same helper script across invocations, bundle it in `scripts/`.

## Structure

1. **Route to deterministic first.** If a CLI/tool exists, the skill is a thin router. Don't duplicate what the tool already does.
2. **One excellent example.** Most relevant language. Complete, runnable, commented WHY. Never multi-language.
3. **Explain WHY, not MUST.** Tell the model why something matters -- it generalises better than rigid commands. If you're writing ALWAYS/NEVER in caps, reframe as reasoning.
4. **Flowcharts only for non-obvious decisions.** Reference material = tables. Linear steps = numbered list.
5. **Gotchas table** for things agents get wrong without the skill.
6. **Discipline skills** (TDD, verification) additionally need a rationalization table -- catalogue the excuses agents use and counter each explicitly.

## Naming

- Verb-first or process noun: `condition-based-waiting` not `async-test-helpers`
- Gerunds for processes: `creating-skills`, `debugging-with-logs`
- Letters, numbers, hyphens only in frontmatter `name` field

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Narrative ("In session X, we found...") | State the rule, not the story |
| Template with blanks | One real example to adapt |
| Five languages | One language, ported on demand |
| Generic labels (step1, helper2) | Semantic names always |
| Description mirrors body | Description = trigger only |
| Heavy-handed MUSTs | Explain why; reasoning > commands |
| Reference docs inline | Move to `references/`, point from body |
