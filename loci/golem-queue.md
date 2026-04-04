# Golem Task Scratchpad

> This file is a **planning scratchpad** only. It is NOT in the dispatch path.
> Dispatch via `golem_dispatch` MCP tool (action=dispatch) or direct `golem` CLI.
> Check status: `golem_dispatch action=list`

## Ideas (not yet dispatched)

- Extract shared Google auth module (gmail.py + circadian_clock.py dedup)
- Add description/location support to circadian_clock.schedule_event
- Retire fasti Rust binary (circadian MCP replaces it)

## Dispatched (2026-04-04)

| Workflow ID | Task |
|-------------|------|
| golem-zhipu-0f3f0d6f | golem shell-safety bugs (--task/--tag flags, ASCII sanitization) |
| golem-zhipu-3001eba2 | phenotype_rename: smarter tmux tab token extraction |
| golem-zhipu-6fec67a3 | gmail: HTML style/script stripping |
| golem-zhipu-5492fda0 | gmail: file attachment in send_email |
| golem-zhipu-d4e70841 | endosomal: fix invoke_organelle test mocks |
| golem-zhipu-2ebcc391 | regulatory-capture: BRDR rebuild |

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
