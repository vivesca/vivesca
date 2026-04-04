# Golem Task Scratchpad

> **Planning only.** Nothing reads this file for execution.
> Sole dispatch path: `golem_dispatch` MCP tool (action=dispatch).
> The markdown poller (`dispatch.py --poll`) was retired 2026-04-04.

## Ideas (not yet dispatched)

- Write `assays/test_gmail.py` — smoke test for search/get_thread/get_message/archive/mark_read (mock the Google API service, verify batch uses `svc.new_batch_http_request()` not `BatchHttpRequest()`)
- Sweep: remove `from __future__ import annotations` from all 184 files in `src/` — unnecessary on Python 3.14 (PEP 649). Pure deletion, no logic changes. Run ruff after to confirm no breakage.
- Extract shared Google auth module (gmail.py + circadian_clock.py dedup)
- Add description/location support to circadian_clock.schedule_event
- Retire fasti Rust binary (circadian MCP replaces it)

### Pending

- [!] `golem [t-e38489] --provider zhipu [t-fix001] "Fix assays/test_cytokinesis.py and assays/test_enzymes_cytokinesis.py -- they import GatherResult and cytokinesis_gather from metabolon.enzymes.cytokinesis but those were removed. Read src/metabolon/enzymes/cytokinesis.py to see what is actually exported (CytoResult, cytokinesis). Update both test files to test the actual current API. Remove references to GatherResult/cytokinesis_gather. Run: cd ~/germline && uv run pytest assays/test_cytokinesis.py assays/test_enzymes_cytokinesis.py -v --tb=short (retry)"`
- [!] `golem [t-57a977] --provider zhipu [t-fix002] "Fix assays/test_organelles_circadian_clock.py and assays/test_resources_circadian.py -- they import _gog from metabolon.organelles.circadian_clock but it was removed. Read src/metabolon/organelles/circadian_clock.py to see the current API. Update test imports to match what actually exists. Run: cd ~/germline && uv run pytest assays/test_organelles_circadian_clock.py assays/test_resources_circadian.py -v --tb=short (retry)"`
- [!] `golem [t-9cd465] --provider zhipu [t-fix003] "Fix assays/test_soma_watchdog_observability.py -- it references JSONL_PATH which was removed from the soma_watchdog module. Read the actual source (grep for soma_watchdog in src/metabolon/ to find it), check what constants exist now, update the test to use the current API. Run: cd ~/germline && uv run pytest assays/test_soma_watchdog_observability.py -v --tb=short (retry)"`

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
- [!] `golem [t-f5515e] --provider zhipu [t-fix001] "Fix assays/test_cytokinesis.py and assays/test_enzymes_cytokinesis.py -- they import GatherResult and cytokinesis_gather from metabolon.enzymes.cytokinesis but those were removed. Read src/metabolon/enzymes/cytokinesis.py to see what is actually exported (CytoResult, cytokinesis). Update both test files to test the actual current API. Remove references to GatherResult/cytokinesis_gather. Run: cd ~/germline && uv run pytest assays/test_cytokinesis.py assays/test_enzymes_cytokinesis.py -v --tb=short (retry)"`
- [!] `golem [t-30a083] --provider zhipu [t-fix002] "Fix assays/test_organelles_circadian_clock.py and assays/test_resources_circadian.py -- they import _gog from metabolon.organelles.circadian_clock but it was removed. Read src/metabolon/organelles/circadian_clock.py to see the current API. Update test imports to match what actually exists. Run: cd ~/germline && uv run pytest assays/test_organelles_circadian_clock.py assays/test_resources_circadian.py -v --tb=short (retry)"`
- [!] `golem [t-9a9065] --provider zhipu [t-fix003] "Fix assays/test_soma_watchdog_observability.py -- it references JSONL_PATH which was removed from the soma_watchdog module. Read the actual source (grep for soma_watchdog in src/metabolon/ to find it), check what constants exist now, update the test to use the current API. Run: cd ~/germline && uv run pytest assays/test_soma_watchdog_observability.py -v --tb=short (retry)"`
