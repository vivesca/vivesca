# Automated Garden Pipeline — Brainstorm

**Date:** 2026-03-07
**Status:** Draft

## What We're Building

An automated content pipeline for terryli.hm that removes the manual approval gate between session insight and published post. When Claude detects a publishable idea during a session, it drafts, validates with judge, and publishes automatically — no explicit "should we post this?" prompt needed.

This has two phases:
- **Phase 1 (session-triggered):** Claude publishes autonomously when an insight surfaces in a live session and judge passes. No human approval step.
- **Phase 2 (headless):** A LaunchAgent or cron pulls from a topic queue, generates posts independently of any active session, validates, and publishes.

## Why This Approach

The current friction point is the approval gate — "garden post?" → Terry says yes → write → judge → Terry says publish. That gate was appropriate when publishing felt risky. With judge now validating quality and voice, the gate is redundant overhead.

Session-triggered automation is the natural first step: Claude already spots publishable insights, the judge criteria are defined, and sarcio publish is a one-liner. The only change is removing the "please confirm" step.

## Key Decisions

**Trigger:** Session insights — Claude detects publishable moments during live sessions. No cron or queue for Phase 1.

**Review gate:** Full auto — generate → judge → publish. Terry reviews after it's live. A Telegram notification from `deltos` confirms what was posted.

**Quality gate:** judge with `article` criteria. If `needs_work`: one revision pass. If still failing: flag to Terry rather than publish. Never publish a failing post silently.

**Voice consistency:** blog/CLAUDE.md is the style reference. Posts generated from session insights inherit session context — no hallucination risk since the content comes from the live conversation.

**Phase 2 trigger:** Topic queue at `~/notes/Writing/Blog/Queue.md`. Each entry: topic, angle, optional seed notes. LaunchAgent runs daily (morning), picks the top unprocessed entry, generates, judges, publishes, and marks as done.

## Phase 1 Architecture

```
Session insight detected
    ↓
sarcio new "<title>"
    ↓
Claude drafts (blog/CLAUDE.md style)
    ↓
judge (article criteria)
    ↓ pass              ↓ needs_work
sarcio publish      One revision → judge again
    ↓                   ↓ pass        ↓ fail
Telegram notify     publish       Flag to Terry (deltos)
```

## Phase 2 Architecture (future)

```
LaunchAgent (daily, 8am)
    ↓
Read ~/notes/Writing/Blog/Queue.md — pick top entry
    ↓
Claude API call: generate post (style: blog/CLAUDE.md)
    ↓
Claude API call: judge (article criteria)
    ↓ pass              ↓ fail after 1 revision
sarcio publish      Skip entry, flag via Telegram
    ↓
Mark entry as [done] in queue
    ↓
Telegram notification with title + terryli.hm link
```

## Open Questions

- **Phase 2 model:** Which model for headless generation? Sonnet 4.6 for drafting, Haiku for judge to save cost?
- **Queue format:** Simple markdown checklist in `Queue.md`, or a structured YAML/TOML file that sarcio can consume natively?
- **Failure handling in Phase 2:** If judge fails twice, skip silently or notify + keep entry at top of queue?
- **Rate:** No cap — judge is the only gate. Publish whenever it passes.

## Resolved Questions

- **Trigger:** Session insights (not scheduled or queue-only) for Phase 1
- **Review gate:** Full auto — no human approval before publish
- **Notification:** Telegram (deltos) after publish, so Terry knows what went live
- **Rate:** No cap — judge is the only gate. Quality, not frequency, determines what ships.

## What This Is Not

- Not a replacement for high-effort posts (those still go through consilium)
- Not a social media scheduler
- Phase 2 is explicitly future scope — Phase 1 only for now

## Related

- `sarcio` skill — publishing CLI
- `judge` skill — quality gate
- `~/code/blog/CLAUDE.md` — prose style guide
- `~/notes/terryli.hm.md` — garden index
