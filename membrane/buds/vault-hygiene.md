---
name: vault-hygiene
description: Find orphan notes, duplicates, stale refs, broken links in ~/notes vault.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Audit ~/notes vault health. Run once weekly.

1. ORPHANS: find notes with no inbound links and no recent access
   - `cd ~/notes && git log --diff-filter=A --since="90 days ago" --name-only --format='' | sort -u` — new files
   - Cross-reference: grep -r for filenames in other notes — zero hits = orphan candidate

2. DUPLICATES: find notes with very similar titles
   - `ls ~/notes/**/*.md | sort` — look for near-duplicates by filename pattern
   - Flag pairs for manual review, don't auto-delete

3. STALE REFS: find internal links pointing to non-existent files
   - Grep for `[[` wiki-links and `](` markdown links
   - Check if target file exists

4. SIZE OUTLIERS: notes > 50KB may need splitting
   - `find ~/notes -name "*.md" -size +50k`

5. STALE DATED NOTES: files in Daily/ older than 90 days that were never archived

Output per category: list of filenames + reason. Max 5 per category.
Recommend: archive, merge, or split. Never auto-delete.
