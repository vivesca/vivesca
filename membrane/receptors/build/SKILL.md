---
name: build
description: Development lifecycle — on-ramp through propagation. Phase-routed.
user_invocable: true
triggers:
  - nucleation
  - transcription
  - translation
  - folding
  - chaperone
  - build
  - implement
  - design
  - plan
context: fork
model: sonnet
---

# /build

Development lifecycle — on-ramp through propagation. Phase-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Starting a new task | **nucleation** | Structured on-ramp — KB check, research, plan, delegate | `nucleation.md` |
| Designing before building | **transcription** | Collaborative design — one question at a time | `transcription.md` |
| Creating implementation plan | **translation** | Turn design into TDD steps, exact paths, code | `translation.md` |
| Executing a plan | **folding** | Execute implementation — delegate, verify, review, ship | `folding.md` |
| Post-implementation | **chaperone** | Propagation — ensure changes reach skills, memories, routing | `chaperone.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `nucleation.md` in this directory)
3. Follow the sub-workflow instructions
