---
name: Software apoptosis patterns research
description: Research into patterns for programmed retirement/death of software components — feature flags, dead code detection, self-pruning, graceful degradation, chaos engineering
type: project
---

Researched 2026-03-25. Full findings at `/Users/terry/code/vivesca-terry/chromatin/Reference/apoptosis-software-patterns.md`.

Key findings:

- "Apoptotic Computing" is a real named research area (Roy Sterritt, Ulster University / NASA, ~2002). Core mechanism: heartbeat inversion — component self-destructs on absence of stay-alive signal. Practical implementations in aerospace/robotics only. NASA patent GSC-TOPS-181 exists.

- Meta SCARF: most production-hardened dead code removal. Runtime + static analysis, daily diff generation, auto-merges in high-confidence cases. 100M lines removed over 5 years.

- Uber Piranha: weekly AST-level rewriting that removes stale flag branches from source. Not just flag detection — actually writes the deletion diff. Java/Swift/ObjC.

- Uber Cinnamon: configuration-free adaptive load shedding via PID controller + priority queue. Closest to autonomous graceful degradation in production.

- Tombstones pattern: instrument suspected dead code with log-on-call markers. Un-triggered after observation window = definitively dead.

- Azul Code Inventory: JVM first-call instrumentation, records method-level usage in production.

- Flagger + Istio: automated traffic migration to 0% for old service versions, driven by health metrics.

- Kubernetes TTL-after-finished: native TTL for batch Jobs only, not services.

**Core gap:** No system combines autonomous detection + permanent code-level removal + self-triggered execution without human review. Detection is solved; self-removal is not. The biological metaphor currently maps to necrosis prevention (circuit breakers) and dead-tissue detection, not true programmed self-death.

**Why:** Terry is designing the "apoptosis" capability for Vivesca/actus — the organism's self-pruning mechanism. This research establishes the prior art baseline.
