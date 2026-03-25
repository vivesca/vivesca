# Rule Violation Log

Tracks when a system rule (MEMORY.md, CLAUDE.md, hook) existed but was still violated.
Purpose: surface rules that need upgrading from soft guidance → hard gate (hook).

**Escalation trigger:** 2 entries for the same rule = build a hook. Don't wait for subjective pain.

## Format

| Date | Rule | What happened | Root cause | Fix applied |
|------|------|---------------|------------|-------------|
| 2026-02-26 | "URL or domain-specific request → scan skills list BEFORE any tool call" | agent-browser viewport failed on Eats365 mobile-only site → went to `--help` + WebSearch instead of reading browser-automation skill first | Rule scoped too narrowly to URL/domain requests; didn't cover tool troubleshooting scenarios | Broadened MEMORY.md rule to cover both domain requests AND tool misbehavior |
| 2026-02-27 | "Use `/history` skill for 'what did we discuss about X'. Don't hand-roll JSONL searches." | Spent 10 min hand-rolling Python to search session transcripts, missed 4 of 14 sessions due to `[:10]` truncation. `resurface search --deep` found it in 0.5s. | Ad-hoc code felt faster than recalling the tool. Momentum of "I'll just write a quick script" bypassed the rule. | Strengthened MEMORY.md wording with specific violation example. First violation — watch for recurrence. |
