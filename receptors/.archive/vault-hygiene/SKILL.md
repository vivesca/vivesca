---
name: vault-hygiene
description: Monthly vault maintenance — consolidate Learnings Inbox, archive stale notes, clean up dailies. Use on first Sunday of month alongside /skill-review.
user_invocable: true
---

# Vault Hygiene

Monthly maintenance to keep the vault useful. Consolidates learnings, archives stale content, and surfaces duplicates.

## Trigger

- First Sunday of the month (pair with `/skill-review`)
- When Learnings Inbox exceeds ~30 entries
- After heavy research sessions that generated many notes

## Workflow

### 1. Learnings Inbox Rollup

The inbox is the "Items" layer — atomic facts waiting to be consolidated into "Category" notes.

```bash
wc -l ~/notes/Learnings\ Inbox.md
```

**Review each entry:**

| Action | When |
|--------|------|
| **Consolidate** | Entry relates to existing topic note → merge into that note |
| **Promote** | Entry is substantial → create standalone note, link from inbox |
| **Archive** | Entry was situational, no longer relevant → move to bottom "Archived" section |
| **Keep** | Still fresh, not yet absorbed → leave in inbox |

**Goal:** Inbox should have <15 active entries after cleanup.

### 2. Decay Report

Run the decay report script for structured analysis:

```bash
uv run ~/scripts/vault-decay-report.py
```

This surfaces:
- **Orphans** — Notes with no incoming wikilinks (candidates for linking or archiving)
- **Cold notes** — Notes with access tracking that haven't been touched in 30+ days
- **Tracked notes** — Shows current access counts for people/entity notes

For each flagged note, decide:

| Action | When |
|--------|------|
| **Keep as reference** | Evergreen content (frameworks, credentials, historical records) |
| **Update** | Content is outdated but topic still relevant |
| **Archive** | No longer relevant → move to `~/notes/.archive/` |
| **Delete** | Truly useless (empty stubs, abandoned drafts) |

### 3. Daily Note Archival

Daily notes older than 60 days should be archived unless they contain unique insights not captured elsewhere.

```bash
# List old daily notes
ls -la ~/notes/Daily\ Notes/ 2>/dev/null | head -20
# Or if flat structure:
find ~/notes -name "202[0-9]-[0-9][0-9]-[0-9][0-9]*.md" -mtime +60 | head -20
```

**Archive process:**
1. Scan for any insights not yet in Learnings Inbox or topic notes
2. Extract and consolidate if found
3. Move daily note to `~/notes/.archive/dailies/`

### 4. Duplicate Detection

Surface notes with similar titles or overlapping content:

```bash
# Similar titles
ls ~/notes/*.md | xargs -I{} basename {} | sort | uniq -d

# Notes mentioning same topic
grep -l "interview prep" ~/notes/*.md | head -10
grep -l "job hunting" ~/notes/*.md | head -10
```

**Merge candidates:**
- Multiple prep notes for same company/role
- Overlapping topic notes (e.g., "AI Trends" and "AI News Summary")
- Version suffixes that should be consolidated (v01, v02, draft)

### 5. Link Health Check

Verify key links in CLAUDE.md still resolve:

```bash
grep -o '\[\[.*\]\]' ~/notes/CLAUDE.md | head -20
```

For each link, confirm the target note exists. Fix broken links.

## Output

```markdown
## Vault Hygiene - [Date]

### Learnings Inbox
- **Before:** X entries
- **After:** Y entries
- **Consolidated:** [list of entries merged into topic notes]
- **Promoted:** [new standalone notes created]
- **Archived:** [entries moved to archive section]

### Stale Notes
- **Reviewed:** X notes
- **Archived:** [list]
- **Updated:** [list]
- **Kept as reference:** [list]

### Daily Notes
- **Archived:** X notes from [date range]
- **Insights extracted:** [any salvaged content]

### Duplicates Merged
- [Note A] + [Note B] → [Combined Note]

### Broken Links Fixed
- [[Old Link]] → [[New Link]]

### Next Review
- [ ] Schedule for [first Sunday next month]
```

### 6. Save to Vault

Save review to `/Users/terry/notes/Vault Hygiene - YYYY-MM.md`

## Quick Version (15 min)

For time-constrained sessions:

1. Learnings Inbox only — consolidate top 10 entries
2. Skip stale note scan
3. Skip daily archival
4. Note anything deferred for full review

### 7. QMD Index Update

Keep the semantic search index fresh:

```bash
qmd update        # Re-index changed files
qmd status        # Check index health
qmd embed         # Update embeddings (slow, run in background if many changes)
```

If embeddings are stale (>100 pending), run in background:
```bash
nohup qmd embed > /tmp/qmd-embed.log 2>&1 &
```

### 8. Access Tracking Review

For notes with `type: person` frontmatter, review access patterns:

```bash
grep -l "type: person" ~/notes/*.md | xargs grep -l "access_count"
```

- Notes with `access_count > 5` — Key relationships, keep fresh
- Notes with `last_accessed` > 30 days — Consider if relationship is cooling
- Notes with `access_count = 1` — Barely used, evaluate if worth tracking

## Related

- `/skill-review` — Companion monthly skill audit
- `/daily` — Creates daily notes this skill eventually archives
- `/retro` — Session reflection that feeds Learnings Inbox
- `~/scripts/vault-decay-report.py` — Orphan and cold note detection
