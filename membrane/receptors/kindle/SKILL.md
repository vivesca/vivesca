---
name: kindle
description: Extract Kindle books to markdown via screenshots + Gemini vision. Single book or queue mode.
user_invocable: true
---

# Kindle Extractor Skill

## Trigger
`/kindle`, "kindle extract", "extract book", "scrape kindle", "kindle queue", "extract books overnight"

## What This Does
Extracts Kindle books to markdown via screenshots + Gemini vision.
Two modes:
- **Single book** — extract the currently open book
- **Queue mode** — extract a list of books by ASIN (overnight)

CLI at `~/bin/kindle-extract` (source: `~/code/kindle-extract/`).
Queue file: `~/notes/Books/kindle-queue.txt`

---

## Single Book Mode

### 1. Verify agent-browser is on Kindle
```bash
agent-browser get url
```
Must contain `read.amazon.com`. If not, tell user to open Kindle Cloud Reader first.

### 2. Check resume status
```bash
agent-browser get title
# Parse: "AWAKENINGS | Kindle" → "Awakenings" → ~/notes/Books/Awakenings.md
/usr/bin/grep -c "--- Page" ~/notes/Books/<title>.md 2>/dev/null || echo "0"
```
Report: "Found 46 pages already extracted — will resume from page 47."

### 3. Start
```bash
kindle-extract                    # foreground
kindle-extract --background       # detached tmux session "kindle"
```

### 4. Report to user
```
Running in tmux session "kindle"
Log:    ~/tmp/kindle.log
Attach: tmux attach -t kindle
Stop:   tmux kill-session -t kindle
```

---

## Queue Mode (overnight)

Queue file: `~/notes/Books/kindle-queue.txt`
Format: one ASIN per line, optional comment after whitespace, `#` lines skipped.

```
# Tier 1: Classics
B00CNQ2NTK  # Awakenings - Oliver Sacks
B0041OT9W6  # The Diary of a Young Girl - Anne Frank
```

### Start overnight run
```bash
kindle-extract --queue ~/notes/Books/kindle-queue.txt --background
```

Output:
```
Running in tmux session "kindle"
Log:    ~/tmp/kindle.log
Attach: tmux attach -t kindle
Stop:   tmux kill-session -t kindle
```

### Test first (2 pages per book)
```bash
kindle-extract --queue ~/notes/Books/kindle-queue.txt --end-page 2
```

### Monitor
```bash
tmux attach -t kindle     # live output, detach with Ctrl-a d
```

---

## Getting ASINs

ASINs are embedded in the library page JSON. To extract all:
```bash
agent-browser navigate "https://read.amazon.com/kindle-library"
# wait 3s
agent-browser eval "document.body.innerHTML.match(/asin...([A-Z0-9]{10})/g).join(',')"
```
Cross-reference with the title list from `agent-browser snapshot`.
Curated queue already built at `~/notes/Books/kindle-queue.txt`.

---

## Notes
- Extraction rate: ~2.5s/page → ~23 min/book → ~8 books overnight
- Auto-resumes within each book (scans `--- Page N ---` markers)
- `--end-page` works in both single and queue mode (cap per book)
- `--background` re-execs in detached tmux session "kindle"; kills existing session first
- Default model: `gemini-2.5-flash-lite`
- Mac sleep: not an issue if `caffeinate` is active (`pmset -g | grep sleep`)

## Files
- CLI: `~/bin/kindle-extract` → `~/code/kindle-extract/`
- Queue: `~/notes/Books/kindle-queue.txt`
- Output: `~/notes/Books/`
- Log: `~/tmp/kindle.log`
