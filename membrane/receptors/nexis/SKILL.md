---
name: nexis
description: "Obsidian vault link health — scan, triage broken links, surface orphans. Use when running nexis CLI or triaging vault link issues."
user_invocable: true
cli: nexis
cli_version: 0.2.5
triggers:
  - nexis
  - broken links
  - vault link
  - orphans
  - unlink
  - triage
---

# /nexis — Vault Link Health

Three modes: **scan** (quick health check), **triage** (fix broken links interactively), and **unlink** (bulk-convert stale links to plain text).

## Triggers

- `/nexis` — scan vault, summary view
- `/nexis triage [--folder <subfolder>]` — interactive broken link triage (redirects, placeholders)
- `/nexis orphans` — surface non-noise orphans worth reviewing
- `/nexis unlink` — bulk-convert all stale broken links to plain text (use when triage is overkill)

---

## Mode: Scan

Quick health check. `.nexisignore` at vault root auto-excludes structural noise — no flags needed.

```bash
# Summary (default — counts only, .nexisignore applied automatically)
nexis ~/epigenome/chromatin

# Override: add extra excludes on top of .nexisignore
nexis ~/epigenome/chromatin --exclude "Some Other Dir"
```

**`.nexisignore`** lives at `~/epigenome/chromatin/.nexisignore` — one directory name per line, `#` for comments. Excluded dirs are silently skipped in all scans.

**Interpreting results:**
- Orphans: ~161 after .nexisignore; the real actionable set is ~20-30 notes.
- Broken links: ~109 signal (Archive/noise already excluded by .nexisignore).
- Embeds: Informational — embeds count toward connectivity.

---

## Mode: Triage

Fix broken links interactively. Works on unique *targets* (not sources) — same target broken in 5 files = one decision, one batch fix.

### Step 1: Scope the run

```bash
# Scoped to a subfolder (recommended — avoids noise)
nexis ~/epigenome/chromatin --broken 2>/dev/null | grep "^  <Folder>/"

# Or full vault excluding noise
nexis ~/epigenome/chromatin --exclude Archive --exclude "Waking Up" --broken 2>/dev/null
```

### Step 2: Extract unique broken targets

```bash
nexis ~/epigenome/chromatin --broken 2>/dev/null | grep "^  <Folder>/" \
  | sed 's/.*: //' | sort -u
```

### Step 3: For each unique broken target, classify

For each `[[Target]]`:

1. **Search vault for likely redirect:**
```bash
find ~/epigenome/chromatin -name "*.md" 2>/dev/null \
  | grep -i "<keyword from target>" \
  | grep -v ".obsidian\|Archive"
```

2. **Check if intentional placeholder** — read the source line for context:
```bash
grep -rn "Target" ~/epigenome/chromatin/<Folder>/ 2>/dev/null | head -5
```

3. **Classify as one of:**
   - **Redirect** — note exists under different name → propose rename
   - **Placeholder** — note was planned, never written → leave untouched
   - **Stale/remove** — reference is dead, link adds no value → propose removal

### Step 4: Present batch proposal before touching anything

Present a summary table:

| Target | Classification | Proposed action |
|--------|---------------|----------------|
| `[[Simon Eltringham - HSBC Interview Prep]]` | Redirect | → `[[Simon Eltringham - HSBC Profile]]` (5 files) |
| `[[Decision-Making Under Pressure]]` | Placeholder | Leave — planned note |
| `[[str-relabelling skill]]` | Stale | Remove from Related field |

**Do not make any edits until user confirms the table.**

### Step 5: Apply confirmed fixes

For redirects and removes, use `sed -i ''` to batch-replace across all source files:

```bash
# Redirect
sed -i '' 's/\[\[Old Name\]\]/[[New Name]]/g' file1.md file2.md ...

# Remove from pipe-delimited Related field
sed -i '' 's/ | \[\[Dead Link\]\]//g; s/\[\[Dead Link\]\] | //g' file.md
```

Verify with a follow-up nexis run on the same scope.

---

## Mode: Unlink (v0.2.4+)

Bulk-convert all broken wikilinks to plain text in place. Use when triage is overkill — e.g. stale job hunting archives, literature notes, or after a bulk note rename.

`[[Dead Note]]` → `Dead Note` · `[[Dead Note|Alias]]` → `Alias`

```bash
# Dry-run first — see count without touching files
nexis ~/epigenome/chromatin --exclude Archive --exclude "Waking Up" --unlink --dry-run 2>&1 | grep "Dry run"

# Apply (excludes Archive + Waking Up noise)
nexis ~/epigenome/chromatin --exclude Archive --exclude "Waking Up" --unlink 2>/dev/null

# Verify: should show 0 signal broken links
nexis ~/epigenome/chromatin --exclude Archive --exclude "Waking Up" 2>/dev/null
```

**What it does:**
- Only unlinks links that nexis already flagged as broken (code blocks and HTML comments are safe)
- Redirects (renamed notes) need triage — `--unlink` won't redirect, just de-brackets
- Preserves aliases: `[[Dead|Alias]]` → `Alias` (alias survives, dead bracket gone)

**When to use triage instead:** When broken links might be redirects (renamed notes) that should be re-pointed. `--unlink` is irreversible for redirects — use it on archives and stale references where plain text is fine.

---

## Mode: Orphans

Surface non-noise orphans that might need attention.

**Default:** `.nexisignore` at `~/epigenome/chromatin/.nexisignore` handles permanently terminal dirs automatically. `nexis ~/epigenome/chromatin` reports ~211 orphans (down from 8,113 raw).

**Three categories of orphans:**
- **Permanently terminal** → in `.nexisignore` (dedao-courses, Archive, Daily, etc.)
- **Not yet linked** → surface with `--orphan-days 14`; they'll appear when recently touched
- **Done/closed** → job applications, session artifacts — ignore or add to `.nexisignore`

```bash
# Weekly hygiene — recently active, unconnected (the real working set)
nexis ~/epigenome/chromatin --orphans --orphan-days 14

# Asymmetric links — strongest "should link back" signal
nexis ~/epigenome/chromatin --asymmetry --orphan-days 14

# Full list (all orphans post-.nexisignore)
nexis ~/epigenome/chromatin --orphans
```

**`.nexisignore`** lives at `~/epigenome/chromatin/.nexisignore`. Currently excludes: `dedao-courses`, `Archive`, `Daily`, `Councils`, `Clippings`, `Readwise`, `Waking Up`, `copilot`, `memory`, `opencode-runs`, `Job Scans`, `Consilium Reviews`, `Templates`. Books and Learnings are intentionally NOT excluded — they have synthesis value and should surface when recently touched.

`--orphan-days 7` → orphans modified in the last 7 days (recently active, not yet connected)
`--orphan-days 30` → broader recent window — catches notes that drifted disconnected over the past month

**What's worth acting on:**
- Active project notes with no links (disconnected knowledge)
- Draft posts / articles that were never linked from a hub
- Recent notes (< 30 days) that haven't been connected yet

**What to ignore:**
- Template files, scratch notes, one-off exports
- Books/, Daily/, Archive/ — expected orphans even with `--orphan-days`

---

## Known Patterns

| Pattern | Meaning | Fix |
|---------|---------|-----|
| Note renamed "X - Interview Prep" → "X - Profile" | Rename during transition | Redirect |
| `[[skill-name]]` in vault Related fields | Points to Claude skill, not vault | Remove |
| `[[Note#Section]]` resolves fine (v0.2.1+) | Anchor stripped, stem matched | No action |
| `warning: duplicate stem "X"` (v0.2.3+) | Two notes share same filename in different folders | One wins; the other is unlinkable by `[[X]]` — rename or use path-qualified links |
| Stray `-->` in note without `<!--` opener | Garbled/corrupted content — NOT a comment block | Links below it are real broken links |
| HTML comment `<!-- [[link]] -->` (v0.2.2+) | Stripped before parsing — never false-positive | No action |
| Running `nexis` on subfolder | Cross-folder links appear broken | Always run on vault root, filter by path |
| Archive/Waking Up dominate broken count | Expected noise | Use `--exclude` to see signal |

## Gotchas

- **Never run `nexis ~/epigenome/chromatin/<subfolder>`** — links to notes outside the subfolder will always appear broken. Run on vault root, filter output by path.
- **Broken count drops ~70 with v0.2.1** anchor fix. If seeing high counts on older versions: `cargo install nexis` to upgrade.
- **`--exclude` names match path components exactly** — case-sensitive. `--exclude Archive` works; `--exclude archive` does not.
- **`--exclude` does NOT accept comma-separated values.** `--exclude "Archive,Daily"` passes the literal string "Archive,Daily" and matches nothing. Use separate flags: `--exclude Archive --exclude Daily`.
