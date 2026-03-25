# Wrap Skill: Daily Note Path Bug (Feb 2026)

## Problem

The wrap skill wrote session logs to `~/epigenome/chromatin/Daily/YYYY-MM-DD.md` but the vault stores daily notes flat at `~/epigenome/chromatin/YYYY-MM-DD.md`. Morning and daily skills read the flat path — so all wrap entries were invisible to them.

## Impact

24 daily notes (Jan 2 – Feb 17 2026) had session logs silently written to the wrong location. The flat files either had no Activity section or only entries from the morning skill.

## Root Cause

Line 49 of `~/skills/wrap/SKILL.md` didn't specify the exact path, and the implicit "daily note" concept was ambiguous — Obsidian daily note plugins often use a `Daily/` subfolder, but this vault uses flat structure.

## Fix

Standardised all three skills (wrap, daily, morning) to use `~/epigenome/chromatin/Daily/YYYY-MM-DD.md`. Moved 33 flat daily notes into `~/epigenome/chromatin/Daily/`. Merged content where both versions existed.

## Lesson

Skills that write to vault files should use explicit absolute paths, not conceptual references like "today's daily note." Ambiguity = silent data loss. When multiple skills touch the same files, grep for the path across all skills to ensure consistency.
