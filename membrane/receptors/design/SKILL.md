---
name: design
description: Skill/system creation — create, quality-check, name, decide. Phase-routed.
user_invocable: true
triggers:
  - design
  - create skill
  - ontogenesis
  - maturation
  - hybridization
  - transcription-factor
  - decision
context: fork
model: sonnet
---

# /design

Skill/system creation — create, quality-check, name, decide. Phase-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Create new skill | **ontogenesis** | Design or promote ad-hoc solution into skill | `ontogenesis.md` |
| Quality check | **maturation** | Writing/editing SKILL.md — quality heuristics | `maturation.md` |
| Naming constraint | **hybridization** | Forced bio naming as design constraint | `hybridization.md` |
| Structured decision | **transcription-factor** | Capture decisions with bouncer pattern | `transcription-factor.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `ontogenesis.md` in this directory)
3. Follow the sub-workflow instructions
