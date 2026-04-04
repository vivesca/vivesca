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
