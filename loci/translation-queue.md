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

### vivesca MCP surface slim-in-place (evidence-based)

**Measured 2026-04-05** (see `finding_vivesca_mcp_context_cost.md`): vivesca's actual 46-tool surface is ~2,500 tokens / ~1.25% of context, NOT the "tens of thousands" cited in published benchmarks. The original 55-tool migration scope was based on theoretical arguments that don't describe this system. Rescoped to the actual hotspots.

**Scope: 9 heavy tools (schema ≥ 300 chars) contribute 51% of the surface.** Target them specifically. Leave the 31 tiny tools (< 150 chars) alone — migrating them saves ~893 tokens at the cost of 31 ribosome tasks = theater.

**Approach: slim-in-place, not migrate.** The heavy tools (emit, demethylase, chemotaxis, endosomal, gap_junction, telegram_receptor, ecphory, endocytosis, exocytosis) are heavy because their MCP `description` field contains full action manuals (every sub-verb + required/optional params enumerated inline). The fix: move the action-manual content into the corresponding SKILL.md, leave a terse `action1|action2|action3 — purpose` in the MCP description. Same functionality, ~50% surface reduction, no actual migration.

- **Task 1 — Slim the 9 heavy descriptions** (per-tool atomic edits, CC judgment work not ribosome): for each of `{emit, demethylase, chemotaxis, endosomal, gap_junction, telegram_receptor, ecphory, endocytosis, exocytosis}`:
  - Read the current MCP tool registration and its corresponding skill
  - Identify action-manual content in the description field (anything enumerating sub-verbs + their param requirements)
  - Move that content to the SKILL.md under an "## Actions" or similar section
  - Replace the MCP description with a terse single-line `action1|action2|... — what the tool does overall (≤120 chars per regulon rule)`
  - Verify with unit test that the tool still routes correctly
  - Atomic commit per tool
- **Task 2 — Measure after** — rerun the enumeration script, confirm the total surface dropped from ~2500 to ~1700-1800 tokens. Save updated number to the finding mark.
- **Task 3 — Migrate only if (a-d) all fail.** Any tool whose slimmed description is still >300 chars AND doesn't pass any of the 4 genome criteria (state / complex schema / no-shell harness / needs agent LLM) becomes a migration candidate. Expected scope: 0-4 tools. Most heavy tools will pass criterion (a) state or (d) agent-LLM judgment and stay as MCP.

**Do NOT touch:** ribosome_dispatch (state), ribosome_queue (state), transposase (multi-verb schema), chemotaxis (persistent browser session — SLIM description but KEEP MCP), porta_inject (state), cytokinesis (multi-verb schema), translocation (state), translocon_dispatch (multi-verb schema), censor_evaluate (complex rubric schema).

**Do NOT migrate the 31 tiny tools** (< 150 chars each): lysin, fetch, noesis, rheotaxis, pinocytosis, lysozyme, exauro, tonus, proprioception, interoception, auscultation, integrin, ergometer, mitosis, sporulation, thrombin, necropsy, histone, circadian, differentiation, proteasome, expression, assay, efferens, polarization, ingestion, electroreception_read, exocytosis_push, sortase, and ~2-3 others. Combined schema cost ~900 tokens; migrating them saves nothing meaningful.

**Dispatch path:** Task 1 is judgment work (read, classify, rewrite descriptions, atomic commits) — CC can do it directly in a 60-90 min focused session, or write a per-tool spec and hand to ribosome. Ribosome can do the mechanical parts (description rewrite, commit) but the content decision (what stays inline vs moves to skill) is judgment. Hybrid approach: CC drafts the first 1-2 slim passes as templates, then dispatches the remaining 7 to ribosome with the template as a pattern. Quota permitting (ZhiPu drained 2026-04-05 PM, resets ~midnight HKT).

**Expected outcome:** vivesca MCP surface drops from ~2,500 to ~1,700 tokens (~1% of context from ~1.25%). Useful but marginal gain. The bigger win is the DISCIPLINE: every future tool passes the 4-criterion test, and the top-heavy descriptions stop accumulating action manuals in the schema field.

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
