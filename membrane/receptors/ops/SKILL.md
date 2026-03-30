---
name: ops
description: Domain operations — email, meals, jobs, deliberation, sync, wrap. Domain-routed.
user_invocable: true
triggers:
  - ops
  - email
  - endosomal
  - ingestion
  - lunch
  - adhesion
  - job
  - quorum
  - deliberation
  - mitosis
  - sync
  - cytokinesis
  - wrap
context: fork
model: sonnet
---

# /ops

Domain operations — email, meals, jobs, deliberation, sync, wrap. Domain-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Email triage | **endosomal** | Search, classify, batch-archive noise | `endosomal.md` |
| Meal planning | **ingestion** | Suggest lunch, log what was eaten | `ingestion.md` |
| Job evaluation | **adhesion** | Evaluate LinkedIn job postings for fit | `adhesion.md` |
| Multi-model deliberation | **quorum** | Judgment calls via multiple models | `quorum.md` |
| Git sync | **mitosis** | Sync repos across machines | `mitosis.md` |
| Session wrap | **cytokinesis** | Consolidate while context is hot | `cytokinesis.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `endosomal.md` in this directory)
3. Follow the sub-workflow instructions
