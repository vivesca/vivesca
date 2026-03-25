# Vesper Evening Push — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A 9:30pm LaunchAgent that sends a Telegram push with tomorrow's 3 most important things — calendar events, hard deadlines, optional job signal.

**Architecture:** Python uv script (`~/bin/vesper`) fetches tomorrow's calendar via `gog`, parses Praxis.md for due items, optionally reads today's speculor output for strong matches, formats a ≤3-bullet Telegram message, and sends via `deltos`. A LaunchAgent fires it at 9:30pm HKT daily.

**Tech Stack:** Python 3.13 (uv script), subprocess calls to `gog` and `deltos`, regex for TODO parsing.

**Spec:** `~/docs/superpowers/specs/2026-03-10-daily-loop-design.md`

---

## Chunk 1: Core Script

### Task 1: Scaffold `~/bin/vesper`

**Files:**
- Create: `~/bin/vesper`

- [ ] **Step 1: Create the script skeleton with --dry-run support**

```python
#!/usr/bin/env -S uv run --script --python 3.13
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

"""vesper — 9:30pm evening push: tomorrow's 3 big things → Telegram"""

import subprocess, json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HKT = timezone(timedelta(hours=8))
TODAY = datetime.now(HKT)
TOMORROW = TODAY + timedelta(days=1)
TOMORROW_STR = TOMORROW.strftime("%Y-%m-%d")
TOMORROW_LABEL = TOMORROW.strftime("%a %b %-d")
TODO_PATH = Path("/Users/terry/notes/Praxis.md")
VAULT_DIR = Path("/Users/terry/notes/Job Hunting")

DRY_RUN = "--dry-run" in sys.argv


def send(msg: str) -> None:
    if DRY_RUN:
        print("=== DRY RUN ===")
        print(msg)
        return
    subprocess.run(["deltos", msg], check=True)


def main() -> None:
    bullets = []
    bullets += calendar_bullets()
    bullets += todo_bullets(max_items=max(0, 2 - len(bullets)))
    bullets += job_bullets(max_items=max(0, 1 - max(0, len(bullets) - 1)))
    bullets = bullets[:3]  # hard cap

    if not bullets:
        return  # nothing to say tonight

    header = f"🌙 *Tomorrow — {TOMORROW_LABEL}*"
    body = "\n".join(bullets)
    send(f"{header}\n\n{body}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script is executable and parses**
```bash
chmod +x ~/bin/vesper
python3 -m py_compile ~/bin/vesper && echo "OK"
```
Expected: `OK`

- [ ] **Step 3: Run dry-run (skeleton, no functions yet)**
```bash
~/bin/vesper --dry-run
```
Expected: exits cleanly (no bullets yet, no output)

- [ ] **Step 4: Commit skeleton**
```bash
cd ~/officina && git add bin/vesper && git commit -m "feat(vesper): scaffold evening push script"
```

---

### Task 2: Calendar bullets

**Files:**
- Modify: `~/bin/vesper` (add `calendar_bullets()`)

- [ ] **Step 1: Add calendar_bullets() after the constants block**

```python
def calendar_bullets() -> list[str]:
    """Fetch tomorrow's calendar events → formatted bullets."""
    result = subprocess.run(
        ["gog", "calendar", "list",
         "--from", TOMORROW_STR, "--to", TOMORROW_STR, "-j"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    events = data.get("events", [])
    bullets = []
    for e in events:
        summary = e.get("summary", "").strip()
        if not summary:
            continue
        start = e.get("start", {})
        dt_str = start.get("dateTime", "")
        if dt_str:
            dt = datetime.fromisoformat(dt_str).astimezone(HKT)
            time_label = dt.strftime("%-I:%M%p").lower()
            bullets.append(f"📅 {time_label} {summary}")
        else:
            bullets.append(f"📅 {summary}")  # all-day event
    return bullets
```

- [ ] **Step 2: Test calendar fetch**
```bash
~/bin/vesper --dry-run
```
Expected: prints tomorrow's calendar events as `📅 HH:MMam Title` lines (or empty if no events tomorrow)

- [ ] **Step 3: Verify against known event (AIA interview is Mar 12)**
```bash
# Temporarily override TOMORROW to Mar 12 to verify
python3 -c "
import subprocess, json
from datetime import datetime, timezone, timedelta
r = subprocess.run(['gog','calendar','list','--from','2026-03-12','--to','2026-03-12','-j'], capture_output=True, text=True)
data = json.loads(r.stdout)
for e in data.get('events', []):
    print(e.get('summary'), e.get('start',{}).get('dateTime'))
"
```
Expected: sees AIA Interview at 09:45

- [ ] **Step 4: Commit**
```bash
cd ~/officina && git add bin/vesper && git commit -m "feat(vesper): add calendar bullets"
```

---

### Task 3: TODO deadline bullets

**Files:**
- Modify: `~/bin/vesper` (add `todo_bullets()`)

- [ ] **Step 1: Add todo_bullets() — parse Praxis.md for due: tags**

```python
def todo_bullets(max_items: int = 2) -> list[str]:
    """Scan Praxis.md for items due tomorrow or overdue."""
    if max_items <= 0 or not TODO_PATH.exists():
        return []

    text = TODO_PATH.read_text()
    bullets = []
    # Match unchecked items with due: tag
    for line in text.splitlines():
        if not line.strip().startswith("- [ ]"):
            continue
        m = re.search(r"due:(\d{4}-\d{2}-\d{2})", line)
        if not m:
            continue
        due_date = m.group(1)
        if due_date > TOMORROW_STR:
            continue  # future, skip
        # Extract readable title: text between "- [ ]" and first backtick/tag
        title = re.sub(r"`[^`]*`", "", line)         # remove inline code
        title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)  # unwrap bold
        title = re.sub(r"due:\S+", "", title)         # remove due tag
        title = re.sub(r"—.*$", "", title)            # cut trailing em-dash notes
        title = title.lstrip("- [ ]").strip()
        title = re.sub(r"\s+", " ", title).strip()
        if not title or len(title) < 5:
            continue
        overdue = due_date < TODAY.strftime("%Y-%m-%d")
        prefix = "⚠️" if overdue else "📋"
        bullets.append(f"{prefix} {title[:60]}")
        if len(bullets) >= max_items:
            break
    return bullets
```

- [ ] **Step 2: Test TODO parsing**
```bash
~/bin/vesper --dry-run
```
Expected: sees items like `📋 Book Jeff Law Physio` or `⚠️ Dental cleaning with Dr Mark Au`

- [ ] **Step 3: Commit**
```bash
cd ~/officina && git add bin/vesper && git commit -m "feat(vesper): add TODO deadline bullets"
```

---

### Task 4: Job signal bullet (optional slot 3)

**Files:**
- Modify: `~/bin/vesper` (add `job_bullets()`)

- [ ] **Step 1: Add job_bullets() — read today's speculor triage output**

```python
def job_bullets(max_items: int = 1) -> list[str]:
    """If today's speculor note has strong matches, surface count as one bullet."""
    if max_items <= 0:
        return []
    today_str = TODAY.strftime("%Y-%m-%d")
    note_path = VAULT_DIR / f"Job Alerts {today_str}.md"
    if not note_path.exists():
        return []
    text = note_path.read_text()
    # Count lines under ## Strong Match section (before next ##)
    in_strong = False
    count = 0
    for line in text.splitlines():
        if line.strip() == "## Strong Match":
            in_strong = True
            continue
        if in_strong and line.startswith("##"):
            break
        if in_strong and line.strip().startswith("- [ ]"):
            count += 1
    if count == 0:
        return []
    label = "match" if count == 1 else "matches"
    return [f"💼 {count} strong job {label} today"]
```

- [ ] **Step 2: Test full dry-run**
```bash
~/bin/vesper --dry-run
```
Expected: full formatted message with up to 3 bullets, e.g.:
```
=== DRY RUN ===
🌙 *Tomorrow — Wed Mar 11*

📋 Book Jeff Law Physio
⚠️ Dental cleaning with Dr Mark Au
💼 3 strong job matches today
```

- [ ] **Step 3: Commit**
```bash
cd ~/officina && git add bin/vesper && git commit -m "feat(vesper): add job signal bullet"
```

---

## Chunk 2: LaunchAgent + Live Test

### Task 5: LaunchAgent plist

**Files:**
- Create: `~/officina/launchd/com.terry.vesper.plist`
- Symlink: `~/Library/LaunchAgents/com.terry.vesper.plist`

- [ ] **Step 1: Create the plist**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.terry.vesper</string>
	<key>ProgramArguments</key>
	<array>
		<string>/Users/terry/bin/vesper</string>
	</array>
	<key>EnvironmentVariables</key>
	<dict>
		<key>PATH</key>
		<string>/opt/homebrew/bin:/Users/terry/.local/bin:/usr/local/bin:/usr/bin:/bin</string>
	</dict>
	<key>StandardErrorPath</key>
	<string>/Users/terry/logs/cron-vesper.log</string>
	<key>StandardOutPath</key>
	<string>/Users/terry/logs/cron-vesper.log</string>
	<key>StartCalendarInterval</key>
	<dict>
		<key>Hour</key>
		<integer>21</integer>
		<key>Minute</key>
		<integer>30</integer>
	</dict>
</dict>
</plist>
```

- [ ] **Step 2: Symlink and load**
```bash
ln -sf ~/officina/launchd/com.terry.vesper.plist ~/Library/LaunchAgents/com.terry.vesper.plist
launchctl load ~/Library/LaunchAgents/com.terry.vesper.plist
launchctl list com.terry.vesper
```
Expected: entry appears in launchctl list (PID may be `-` since it's time-triggered)

- [ ] **Step 3: Commit plist**
```bash
cd ~/officina && git add launchd/com.terry.vesper.plist && git commit -m "feat(vesper): add LaunchAgent at 21:30 HKT"
```

---

### Task 6: Live Telegram test

- [ ] **Step 1: Send a real test message**
```bash
~/bin/vesper
```
Expected: Telegram receives the message within a few seconds. Check `@TekmarBot`.

- [ ] **Step 2: Verify log file**
```bash
cat ~/logs/cron-vesper.log
```
Expected: clean output or empty (script only logs on error)

- [ ] **Step 3: Add vesper skill**
```bash
mkdir -p ~/skills/vesper
```
Create `~/skills/vesper/SKILL.md` with: what it does, 9:30pm schedule, dry-run flag, log path, how to update the 3-bullet filter.

- [ ] **Step 4: Commit skill + push everything**
```bash
cd ~/skills && git add vesper/ && git commit -m "feat: add vesper skill" && git push
cd ~/officina && git push
```

---

## Verification Criteria

- `~/bin/vesper --dry-run` prints a well-formed message with ≤3 bullets
- `~/bin/vesper` sends a real Telegram message to `@TekmarBot`
- `launchctl list com.terry.vesper` shows the agent loaded
- Message is clean: no padding, no noise, only genuine tomorrow items
- If nothing due tomorrow, script exits silently (no empty message sent)
