# Ribosome Task Scratchpad

> **Planning only.** Nothing reads this file for execution.
> Sole dispatch path: `ribosome_dispatch` MCP tool (action=dispatch).
> The markdown poller (`dispatch.py --poll`) was retired 2026-04-04.

## Ideas (not yet dispatched)

- Write `assays/test_gmail.py` — smoke test for search/get_thread/get_message/archive/mark_read (mock the Google API service, verify batch uses `svc.new_batch_http_request()` not `BatchHttpRequest()`)
- Sweep: remove `from __future__ import annotations` from all 184 files in `src/` — unnecessary on Python 3.14 (PEP 649). Pure deletion, no logic changes. Run ruff after to confirm no breakage.
- Extract shared Google auth module (gmail.py + circadian_clock.py dedup)
- Add description/location support to circadian_clock.schedule_event
- Retire fasti Rust binary (circadian MCP replaces it)

### [POST-CAPCO] MCP → CLI migration campaign

Driver: refined genome rule "don't auto-wrap every CLI in MCP — that's theater". Willison (Oct/Nov 2025) + Cloudflare Code Mode (Feb 2026) confirm direction. Target: shrink vivesca MCP surface from ~75 tools to ~15-20, reduce session cold-start + fragility blast radius, improve cross-client portability (Codex/Gemini/Goose).

- **Phase 1 — AUDIT** (CC writes, not ribosome): enumerate all vivesca MCP tools; for each, classify as KEEP (persistent state, complex typed schema, or cross-client distribution) or MIGRATE (stateless single-verb / single-param lookup / status read). Output: `~/germline/loci/plans/mcp-to-cli-migration.md` with per-tool verdict + rationale. Target KEEP list: chemotaxis, porta_inject, ribosome_dispatch, ribosome_queue, cytokinesis, transposase, translocation, translocon_dispatch, censor_evaluate, endosomal, endocytosis, ingestion, assay (plus ~3-5 edge cases).
- **Phase 2 — SKILL AUDIT** (CC): for each MIGRATE tool, verify a skill exists that covers its when/how/why. Write missing skills first. Without the skill layer, removing the MCP tool breaks discovery.
- **Phase 3 — RIBOSOME BATCH** (per-domain sub-batches, 3-5 tools each): for each MIGRATE tool: (a) confirm underlying CLI/effector exists and has `--help` + `--json`; build or improve if not; (b) remove MCP registration from vivesca server; (c) update or create the skill to reference the CLI; (d) run assay to confirm nothing calls the removed MCP name. Atomic commit per tool. Tests gate each.
- **Phase 4 — VERIFY**: integrin scan + session test with Codex and Gemini CLIs to confirm CLI + skill path works across harnesses.

Suggested domain batches for Phase 3:
  1. Read-only lookups: lysin, fetch, noesis, rheotaxis, pinocytosis, lysozyme, exauro
  2. Status reads: tonus, proprioception, interoception, auscultation, integrin, ergometer
  3. Single-verb actions: emit, efferens, mitosis, sporulation, thrombin, necropsy, demethylase
  4. Domain workflows (review carefully — some may need KEEP): histone, circadian, differentiation, proteasome, expression, exocytosis
  5. Communication: gap_junction, telegram_receptor, electroreception_read

Do NOT touch: ribosome_dispatch, ribosome_queue, transposase, chemotaxis, porta_inject, cytokinesis, translocation, translocon_dispatch, censor_evaluate. These pass all three criteria.

### Pending

(none — t-fix001, t-fix002, t-fix003 completed by CC during ribosome rename)

## Completed (2026-04-04)

- golem-zhipu-0f3f0d6f — golem shell-safety bugs
- golem-zhipu-3001eba2 — phenotype_rename: smarter tmux tab token extraction
- golem-zhipu-6fec67a3 — gmail: HTML style/script stripping
- golem-zhipu-5492fda0 — gmail: file attachment in send_email
- golem-zhipu-d4e70841 — endosomal: fix invoke_organelle test mocks
- golem-zhipu-2ebcc391 — regulatory-capture: BRDR rebuild

## Completed (historical)

- t-a68919 — cytokinesis gather report
- t-a869e4 — golem-daemon early kill
- t-c5c3ee — soma-health CPU check
- t-744a2b — golem-daemon dedup guard
- t-be76a0 — temporal post-golem verification gate
- t-61b002 — golem wall-limit
- t-df1e60 — temporal partial-progress detection
- t-c5eef9 — temporal poller stalling fix
- t-ca2248 — temporal stale failure cache fix
- t-ff66cc — temporal auto git sync
- t-4376dc — golem_dispatch MCP enzyme
- t-e01d4e — golem syntax pre-check
