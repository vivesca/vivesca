---
name: produce
description: Content pipeline — forge, process, classify, package, generate. Stage-routed.
user_invocable: true
triggers:
  - produce
  - write
  - article
  - expression
  - metabolize
  - phagocytosis
  - secretion
  - morphogenesis
  - generate image
context: fork
model: sonnet
---

# /produce

Content pipeline — forge, process, classify, package, generate. Stage-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Forge consulting IP | **expression** | Weekly career compound machine | `expression.md` |
| Process articles | **metabolize** | Read, extract, write cards from articles | `metabolize.md` |
| Classify + extract | **phagocytosis** | Classify content, extract insights, save note | `phagocytosis.md` |
| Package deliverable | **secretion** | Quality-gate, format, deliver | `secretion.md` |
| Generate image | **morphogenesis** | Generate images via Gemini models | `morphogenesis.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `expression.md` in this directory)
3. Follow the sub-workflow instructions
