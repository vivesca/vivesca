---
name: speculor
description: Daily LinkedIn job alert collector and AI triage tool. Use when checking job alerts, running triage, or troubleshooting speculor output.
---

# speculor

Daily LinkedIn job collector + AI triage. LaunchAgent fires noon HKT.

## Commands

```bash
speculor                          # collect: Gmail alerts + saved jobs → vault note
speculor triage                   # triage today's vault note via claude-haiku
speculor triage --date 2026-03-10 # triage a specific date
```

## Output

Vault note: `~/epigenome/chromatin/Job Hunting/Job Alerts YYYY-MM-DD.md`

4 tiers after triage:
- **Strong Match** — HK/SG, great fit (AI/DS leadership, model governance, consulting)
- **Review** — HK/SG, partial fit or unclear seniority
- **Skip** — clearly not a fit (CTO ops, junior, quant trading, pure audit)
- **Overseas Watch** — strong role but UK/AU/CA/NZ/etc — keep for monitoring

## LaunchAgent

`com.terry.speculor` — noon HKT daily
Runs: `speculor && speculor triage || true`
Log: `~/logs/cron-speculor.log`

Reload after plist changes:
```bash
launchctl unload ~/Library/LaunchAgents/com.terry.speculor.plist
launchctl load ~/Library/LaunchAgents/com.terry.speculor.plist
```

## Files

- Binary: `~/bin/speculor` (Rust, built from `~/code/speculor/`)
- Plist: `~/officina/launchd/com.terry.speculor.plist`
- Vault output: `~/epigenome/chromatin/Job Hunting/Job Alerts YYYY-MM-DD.md`

## Triage profile

Scoring criteria baked into the binary (`TRIAGE_SYSTEM_PROMPT` in `src/main.rs`):
- **Strong:** HK/SG + AI/ML leadership, model governance, consulting AI/data, VP/AVP/Head/Principal level
- **Skip triggers:** CTO/COO, junior/associate, quant trading, pure IT audit, non-FS engineering
- **Overseas:** UK, AU, CA, NZ — good role but wrong geography for now

To update the profile: edit `src/main.rs`, `cargo build --release -p speculor`, `cp ~/code/target/release/speculor ~/bin/speculor`.

## Gotchas

- `claude -p` inside a Claude Code session fails with "nested session" error — binary strips `CLAUDECODE` env var to bypass this.
- Triage re-runs safely on already-triaged notes (parser handles bold + rationale suffixes).
- CCB Asia duplicate jobs (same role, two job IDs) — triage classifies both independently; usually one skip, one review.
- **Salary range overlap ≠ skip** — triage sometimes downgrades roles where the floor (HKD 100K) is above the salary band bottom. Correct logic: if the range top is at or above floor, it's acceptable (negotiable). Only skip if the *ceiling* is below floor. If `TRIAGE_SYSTEM_PROMPT` produces false negatives on governance/strategy roles, add this explicitly. (Confirmed: SP003 StanChart AI Governance mis-triaged weak→should be strong, Mar 2026)

## Calibration

After a week of runs, flag miscategorizations and update `TRIAGE_SYSTEM_PROMPT`. Common edge cases:
- Recruiter-posted roles (Aquis, Gravitas) — seniority unclear from title alone → Review is correct
- "Professional" in title usually = junior-to-mid → skip or review

## Future

**Per-job company research (legatus):** After triage, dispatch a legatus agent per Strong Match to web-search the company and write a 3-bullet briefing to vault. Revisit when job search becomes primary (not a hedge). Trigger: Capco not working after 3 months, or Strong Match count spikes to 5+/day.
