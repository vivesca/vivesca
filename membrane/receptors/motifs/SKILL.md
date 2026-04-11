---
name: motifs
description: Shared skill patterns — conserved mechanisms reused across many skills. Consult when building or reviewing skills. "shared pattern", "common motif"
user_invocable: false
---

# Motifs — Conserved Skill Patterns

Like conserved sequence motifs in biology, these are structural patterns found across many skills. Skills reference them instead of duplicating.

## Available Motifs

- **[state-branch.md](state-branch.md)** — Gather all state before branching. For skills with 3+ paths.
- **[audit-first.md](audit-first.md)** — Produce a map before modifying. The map IS the spec.
- **[verify-gate.md](verify-gate.md)** — Evidence before assertions. Run, read output, then claim.
- **[check-before-build.md](check-before-build.md)** — Search existing tools before creating new ones.
- **[escalation-chain.md](escalation-chain.md)** — Try simple first, escalate on failure. Log which tier worked.

## How to use from a skill

```markdown
For the decision tree, follow the [state-branch](../motifs/state-branch.md) pattern.
```

Skills reference motifs; they don't copy them. One update to the motif benefits every skill that uses it.

## Adding a new motif

A pattern qualifies as a motif when:
1. It appears in 3+ skills (not just "could be useful someday")
2. It has clear rules (not just "be careful")
3. It has anti-patterns (what goes wrong when you skip it)
