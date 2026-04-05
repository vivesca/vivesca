---
name: monthly
description: Monthly maintenance — content digests, skill review, AI deep review, vault hygiene. "monthly", "monthly maintenance", "run monthly"
user_invocable: true
---

# Monthly Maintenance

Everything that runs once a month. Can trigger on first Friday (via `/weekly`) or independently anytime.

## Trigger

- "monthly", "monthly maintenance", "run monthly"
- First Friday of month (prompted by `/weekly`)

## Checklist

Run each section in order. Report results as a summary table at the end.
If any command in this checklist fails, mark that section as "partial" with the failure reason and continue.

### 1. Content Digest

Fetch and extract insights from subscribed YouTube channels.

```bash
# Preview what's new
digest --dry-run

# Run full digest (transcripts + insight extraction)
digest
```
If either command fails, note "Digest unavailable" for this month and continue to section 2.

Output: `~/epigenome/chromatin/Health/{source}/{YYYY-MM} Digest.md`
Sources configured in `~/skills/digest/sources.yaml`.

### 2. AI Thematic Digest

Generate evidence-grounded thematic digest from archived AI news articles.

```bash
# Preview themes (fast, no synthesis)
uv run ~/skills/endocytosis/ai-digest.py --dry-run

# Full run — produces evidence briefs
uv run ~/skills/endocytosis/ai-digest.py
```
If `uv` or script execution fails, mark AI thematic digest as skipped and continue.

Output: `~/epigenome/chromatin/AI & Tech/YYYY-MM AI Thematic Digest.md`
Prerequisites: endocytosis cron must have been running with article archival (default since Feb 2026).
Cost: ~$0.05-0.15 (Gemini Flash via OpenRouter).

### 3. Theoria Deep Review

Run `/dialexis` in monthly mode (deep review, not weekly synthesis):
- Update Current Landscape section
- Append monthly review entry
- Flag shifts relevant to Capco consulting conversations
- If `/dialexis` is unavailable, add a one-line manual summary from latest weekly snapshot and mark as partial.

### 4. Skill Review

Run `/skill-review`:
- Audit skills for staleness, drift, gaps
- Check skill count and recent changes
- Flag skills not invoked in 30+ days
- If `/skill-review` is unavailable, run a minimal fallback: `ls ~/skills/*/SKILL.md | wc -l` and `git -C ~/skills log --oneline --since="30 days ago"`.

### 5. Source Health Check

Run `endocytosis check` and review broken sources:

```bash
endocytosis check 2>&1 | grep "<-\|(stale)\|x0)"
```
If `endocytosis check` fails, mark source health as unavailable and continue.

- Fix URL-rotted sources (update URLs in `~/.config/endocytosis/sources.yaml`)
- Remove dead sources (domain expired, blog shut down)
- Flag sources with consecutive zeros (`Nx0`) for investigation
- Reference: `~/docs/solutions/endocytosis-reference.md`

~12% source rot rate per quarter. Takes 2-3 min.

### 6. Vault Hygiene

Run inline — no separate skill needed:

a. **Solutions KB** — regenerate index (`python3 ~/scripts/generate-solutions-index.py`) then review for stale or duplicate entries
b. **Decay report** — `uv run ~/scripts/vault-decay-report.py` for orphans/cold notes
c. **Daily note archival** — archive notes >60 days old to `~/epigenome/chromatin/.archive/dailies/`
d. **Broken links** — verify `[[wikilinks]]` in CLAUDE.md still resolve
e. **QMD reindex** — `qmd update && qmd status` (run `qmd embed` in background if stale)
f. **Mark archive rotation** — scan `~/epigenome/marks/archive/` for marks >3 months old with no citations in any session log or MEMORY.md. These are safe to delete permanently (the knowledge is in code/skills/genome). Report count before and after. Also check: any archived mark that was grep-hit during this month's work → promote back to active marks.
If any sub-step fails, record which sub-step failed and continue with the rest.

### 7. Oghma Hygiene

Check for noise from abandoned experiments or stale imports:

```bash
oghma stats
```
If `oghma` or DB access fails, mark Oghma hygiene as unavailable and skip archival actions.

Flag any source with >100 entries that isn't `claude_code`, `opencode`, or `codex` — these are likely stale imports (e.g., MemU, openclaw) that should be archived:

```python
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('~/.oghma/oghma.db'))
c = conn.cursor()
c.execute(\"\"\"SELECT source_tool, COUNT(*) as cnt FROM memories
    WHERE status='active' GROUP BY source_tool HAVING cnt > 100
    ORDER BY cnt DESC\"\"\")
legit = {'claude_code', 'claude-code', 'opencode', 'codex'}
for tool, cnt in c.fetchall():
    flag = '' if tool in legit else ' ⚠️  REVIEW'
    print(f'{tool}: {cnt}{flag}')
conn.close()
"
```

If flagged sources exist, archive them:
```python
# python3 -c "import sqlite3, os; conn = sqlite3.connect(os.path.expanduser('~/.oghma/oghma.db')); conn.execute(\"UPDATE memories SET status='archived' WHERE source_tool='SOURCE_NAME' AND status='active'\"); conn.commit(); print('Done')"
```
If `oghma`/SQLite commands fail, skip archival and report "Oghma hygiene unavailable".

### 8. Finance Check

Quick scan of key financial positions — takes 2 min:

a. **Mortgage rate** — check if any bank is offering ≤2.5% cap (P-2.75% at current SCB prime). Current deal: SCB H+1.3%, cap P-2.75%. Only worth switching if new cap ≤ current cap AND cashback clears the rate difference over the lock-in. Ask Emily (星之谷, WhatsApp) or search current HK mortgage rates. See [[Personal Finance Reference]].

b. **SCB Prime rate** — verify still 5.25% (affects your cap). Check SCB website or `pplx search "Standard Chartered HK prime rate"`.

c. **Credit card balances** — any unpaid statement balances? (CCBA, SCB, BOC)
If rate/search sources are unavailable, note "Finance check partial" and avoid firm recommendations.

### 9. Direction Audit (quarterly — March, June, September, December only)

Read `~/epigenome/chromatin/Life OS.md`. For each domain ask: is this still the right framing? Has anything shifted? Is the listed "next step" still relevant or stale? Update the note in-place — it's a live map, not a historical document. Skip this step in non-quarter months.

### 10. Housekeeping

- Purge orphaned agent files: `/usr/bin/find ~/.claude/todos -name "*.json" -mtime +7 -delete`
- Check MEMORY.md line count (`wc -l`). Flag if >150 — trim or demote to vault.
- **CLAUDE.md tightening pass:** Read every rule and ask two questions: (1) Is this still true? Remove stale references (completed transitions, retired projects, outdated tool names). (2) Does this *need* to be in CLAUDE.md, or does it belong in a skill/solution? Mechanical rules stay. Workflow conventions → relevant skill. Operational gotchas → MEMORY.md. Reusable how-tos → `~/docs/solutions/`. Goal: CLAUDE.md stays thin — rules and pointers only.
- If purge/index commands fail, report "Housekeeping partial" with failed command names.

## Summary Template

After running all sections, present:

```markdown
## Monthly Maintenance — YYYY-MM

| Section | Status | Notes |
|---------|--------|-------|
| Content Digest | X episodes across Y sources | [vault paths] |
| AI Thematic Digest | X themes, Y articles | [vault path] |
| AI Deep Review | Done | [key shifts] |
| Skill Review | X active / Y archived | [changes] |
| Source Health | X broken, Y stale, Z consecutive-zero | [fixes applied] |
| Vault Hygiene | X notes archived, Y orphans | [actions] |
| Finance Check | SCB prime X%, best market cap Y% | [action/no action] |
| Housekeeping | MEMORY.md: X lines, agents purged | [flags] |
```

## Notes

- Total time: ~15-20 min (mostly waiting on digest API calls)
- Digest is the heaviest step — can run backgrounded while doing the rest
- If short on time, at minimum run `/digest` and `/skill-review`

## Boundaries

- Do NOT perform full rewrites of CLAUDE.md/MEMORY.md in this run; flag and queue large restructures.
- Do NOT execute irreversible cleanup beyond the listed housekeeping commands.
- Stop after monthly summary table is produced.

## Example

> Monthly Maintenance — 2026-03 complete. Content and thematic digests generated, AI deep review done, skill review flagged 3 stale skills, and source health found 2 broken feeds. Vault hygiene archived 14 notes; finance check was partial because one rate lookup failed.
