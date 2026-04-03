---
name: parsimonia
description: Essential vs accidental complexity, premature abstraction, when removal is safe. Reference skill for code review, refactoring, and architecture decisions. Not user-invocable.
version: 1
tags: [reference, simplification, complexity, cognition]
triggers: [simplify, refactor, complexity, abstraction, YAGNI, remove, delete, inline, dead code, parsimonia]
disable-model-invocation: true
---

# Parsimonia — Theory of Simplification

> *Parsimonia: Latin "thrift, frugality" — the principle that unnecessary elements should not be multiplied.*

Simplification is **removal of the inessential without losing the essential**. Not shorter. Not easier. The formulation where nothing can be removed without breaking what matters.

Reference skill. Consult during code review (YAGNI checks), refactoring decisions, architecture simplification, or when complexity feels high but you can't articulate why.

## Essential vs Accidental Complexity

Brooks (1986): **essential complexity** is inherent to the problem. **Accidental complexity** is introduced by the solution.

- Remove accidental complexity aggressively
- Respect essential complexity — trying to simplify it just hides it somewhere worse
- A one-line function obscuring a complex business rule isn't simpler — it's the same complexity with worse visibility

**The entire art: telling them apart.**

## Why Things Get Complex

Complexity accumulates through individually reasonable decisions:

| Source | Mechanism | Antidote |
|--------|-----------|----------|
| **Premature abstraction** | Two similar things → shared abstraction → three things (abstraction + two special cases) | Three similar lines > one premature abstraction |
| **Speculative generality** | "What if we need X later?" | YAGNI — epistemological humility about the future |
| **Connascence creep** | Coupling accumulates through accretion | Explicit dependency mapping |
| **Abstraction layering** | Each layer simplifies locally, complicates globally | Count mental models needed to trace one behavior |
| **Loss aversion** | Code exists → has value → keep it | Dead code has negative value — costs attention on every read |

## The Simplicity Test

- **Can I delete this?** Most powerful simplification is removal. Not refactoring — deleting.
- **Can I inline this?** Abstraction only justified when duplication cost > indirection cost.
- **Can a newcomer trace the solution?** If not, accidental complexity is obscuring the logic.
- **Am I naming to hide or reveal?** `processData()` hides. `calculateTaxWithholding()` is long but honest.

## Simplification as Process

1. **First make it work.** Working-but-complex >> elegant-but-broken.
2. **Then make it right.** After you know what the solution actually needs (not what you guessed), accidental complexity becomes visible.
3. **Simplification is revision, not creation.** You can't simplify on first pass — essentiality is discovered through use.

## Failure Modes

| Failure | Description | Signal |
|---------|-------------|--------|
| **Oversimplification** | Removing essential complexity | Edge case bugs, "works for simple case" |
| **Simplicity theater** | Looks simpler, pushes complexity to caller | All callers doing same boilerplate |
| **Refactor addiction** | Simplifying stable, unchanged code | No external trigger for the change |
| **False equivalence** | Two similar things treated as identical | Abstraction has mode flags / special cases |
| **Minimalism as aesthetic** | Pursuing how it looks, not how it works | Removing useful error messages, docs, config |

## The Paradox

Simple solutions are harder to build. Complex solutions are the default — what you get without revision. Simplicity is expensive upfront, cheap to maintain. Complexity is the reverse. Most systems choose cheap upfront and pay forever.

## Human vs Agent

Humans: gestalt ("this whole subsystem is unnecessary") — reasoning about intent. Agents: exhaustive local audit (dead code, single-use abstractions, redundant layers). Best hybrid: agent audits, human evaluates which simplifications are safe.

## When to Consult This Skill

- Code review — is this abstraction justified or premature?
- Refactoring — am I removing accidental complexity or essential?
- Architecture — how many mental models to trace one behavior?
- Post-build — "can it be tighter?" (see tightening-pass pattern)
