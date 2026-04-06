---
name: theoria
description: Automated AI landscape synthesis pipeline (LangGraph + Opus). Use when checking landscape run status, running manual reviews, or debugging pipeline failures.
effort: high
---

# Theoria — Theoria Synthesis Pipeline

Automated AI landscape snapshots at multiple cadences. LangGraph pipeline using `claude --print` (Opus). Named for the Greek official periodic mission dispatched to observe and report.

## When to Use

- Checking if the weekly/monthly landscape ran successfully
- Running a manual landscape review outside the schedule
- Debugging pipeline failures

## Quick Reference

```bash
# Manual run (writes to ~/epigenome/chromatin/Theoria.md and commits)
theoria --period weekly
theoria --period monthly
theoria --period quarterly
theoria --period yearly

# Dry run (prints synthesis to stdout, no file write)
theoria --period weekly --dry-run
```

## Architecture

5-node LangGraph pipeline: Gather → Gap Analysis → Research → Synthesise → Write

**Roll-up architecture** — each cadence synthesizes from the layer below:
- **Weekly:** raw feed (endocytosis log + AI News Log) → weekly snapshot
- **Monthly:** weekly snapshots → thematic synthesis
- **Quarterly:** monthly reviews → strategic assessment
- **Yearly:** quarterly reviews → annual narrative

Nodes:
- **Gather:** weekly reads raw feed; other cadences extract lower-layer snapshots from Theoria.md
- **Gap Analysis:** identifies missing coverage via claude --print
- **Research:** fills top 5 gaps via claude --print (600s timeout)
- **Synthesise:** produces the final snapshot (600s timeout)
- **Write:** appends to Theoria.md, commits to vault git

Conditional edge: if gap analysis returns "NO GAPS", research is skipped.

## Schedule (LaunchAgents)

| Cadence | When | LaunchAgent |
|---------|------|-------------|
| Weekly | Saturday 06:00 | `com.terry.ai-landscape-weekly` |
| Monthly | 1st of month, 12:00 | `com.terry.ai-landscape-monthly` |
| Quarterly | 2nd Jan/Apr/Jul/Oct, 06:00 | `com.terry.ai-landscape-quarterly` |
| Yearly | Jan 3, 06:00 | `com.terry.ai-landscape-yearly` |

Dependency chain: weekly (Sat 06:00, catches US Fri EOB) → monthly (1st noon, after last weekly) → quarterly (2nd) → yearly (3rd).

Logs: `~/logs/cron-ai-landscape-{weekly,monthly,quarterly,yearly}.log`

## Relationship to Other Tools

- **endocytosis** — data collection (upstream). Feeds theoria's gather node via `endocytosis log -n 200`.
- **dialexis skill** — interactive synthesis (parallel). Theoria automates what dialexis does interactively. Both write to `~/epigenome/chromatin/Theoria.md`. dialexis adds governance translation pass + client-specific suggestions that theoria doesn't.
- **weekly skill** — consumer. References Theoria.md output during Friday review.

## Gotchas

- **WebSearch unavailable when nested inside Claude Code.** `claude --print` called from within a Claude Code session can't use WebSearch. LaunchAgent runs (standalone) should have WebSearch available. First Friday run (tonight) will confirm.
- **Timeout:** Research and synthesis nodes have 600s timeout. If a node times out, check log for prompt size — gap analysis may have returned too many items (capped at 5, but the raw articles prompt can also be large).
- **LaunchAgents are copies.** Source: `~/code/theoria/launchd/`. After editing, must `cp` to `~/Library/LaunchAgents/` then `launchctl unload/load`.
- **Package name vs directory.** PyPI package is `theoria`, Python package is `theoria` (in `src/theoria/`), CLI command is `theoria`.

## Files

- Repo: `~/code/theoria/` (GitHub: `terry-li-hm/theoria`, private)
- PyPI: `theoria` (stub reserved)
- Output: `~/epigenome/chromatin/Theoria.md`
- Config: `~/code/theoria/src/theoria/prompts.py` (edit prompt templates here)
