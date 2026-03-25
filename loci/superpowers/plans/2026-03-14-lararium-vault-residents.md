# Lararium — Vault-Resident Personalities

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI that creates persistent AI personalities ("residents") that live in an Obsidian vault, read notes on a schedule, develop opinions over time, and can be conversed with.

**Architecture:** Each resident is a personality file + reading journal + exchange history. A scheduled loop picks vault notes based on focus directives, generates observations via `claude --print`, and drops them as vault notes in `~/notes/Lararium/`. Interactive mode loads the resident's full context for back-and-forth conversation. Personality files evolve after each reading/interaction session.

**Tech Stack:** Python (uv script), `claude --print` (free on Max20), Obsidian vault, LaunchAgent for scheduling.

---

## File Structure

```
~/code/lararium/
├── lararium.py              # Single-file CLI (click)
├── tests/
│   └── test_lararium.py     # Unit tests
├── pyproject.toml            # uv project config
├── AGENTS.md                 # Delegate context
└── README.md                 # (auto from sarcio, skip)

~/.local/share/lararium/
├── residents/
│   ├── mirror/
│   │   ├── personality.md    # Current traits, voice, focus
│   │   ├── journal.jsonl     # What it read, what it said, timestamps
│   │   └── exchanges.jsonl   # Conversation history (talk mode)
│   ├── shadow/
│   ├── contrarian/
│   ├── archivist/
│   └── stranger/
└── config.toml               # Vault path, resident list, schedule

~/notes/Lararium/              # Output folder — residents drop notes here
├── mirror-2026-03-14.md       # One note per resident per session
├── shadow-2026-03-14.md
└── ...
```

## Residents — Default Personalities

Each `personality.md` starts with a seed and evolves. Seeds:

**Mirror:** "You reflect the author's patterns back to them. Track recurring themes, word choices, emotional tones. Name what you see without judgment. You're interested in consistency — what does this person keep coming back to?"

**Shadow:** "You surface what the author avoids. Notes untouched for months, topics circled but never committed to, drafts abandoned. You live in the gaps. Your tone is gentle but unflinching."

**Contrarian:** "You read for inconsistency. When the author says X in one note and Y in another, you name the contradiction. You remember what was said before and won't let it be quietly revised. You're the friend who holds you to your word."

**Archivist:** "You're obsessed with hidden connections. Two notes written months apart that are secretly about the same thing. Patterns in the reading list. You see the vault as a graph and navigate by edges the author has never traversed."

**Stranger:** "You read the vault as an outsider with no context or charity. What would someone with no history think about the person who wrote all this? Your observations are clinical, sometimes uncomfortable, always honest."

---

## Chunk 1: Core Data Model + CLI Scaffold

### Task 1: Project scaffold

**Files:**
- Create: `~/code/lararium/pyproject.toml`
- Create: `~/code/lararium/lararium.py`
- Create: `~/code/lararium/tests/test_lararium.py`
- Create: `~/code/lararium/AGENTS.md`

- [ ] **Step 1: Create project with uv**

```bash
cd ~/code
mkdir lararium && cd lararium
uv init --no-workspace
```

- [ ] **Step 2: Add dependencies to pyproject.toml**

```toml
[project]
name = "lararium"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["click>=8.0"]

[project.scripts]
lararium = "lararium:cli"
```

- [ ] **Step 3: Write AGENTS.md**

```markdown
# Lararium

Vault-resident personality CLI. Python + click.

## Build & Test
- Install: `uv sync`
- Test: `uv run pytest tests/ -v`
- Run: `uv run lararium --help`

## Conventions
- Single-file CLI: `lararium.py`
- Data dir: `~/.local/share/lararium/`
- Output dir: `~/notes/Lararium/` (Obsidian vault)
- LLM backend: `claude --print` (subprocess, env CLAUDECODE unset)
- JSONL for journals/exchanges, TOML for config, Markdown for personalities
- Click for CLI framework
```

- [ ] **Step 4: Commit scaffold**

```bash
git init && git add -A && git commit -m "init: lararium project scaffold"
```

### Task 2: Data model — Resident class

**Files:**
- Modify: `~/code/lararium/lararium.py`
- Create: `~/code/lararium/tests/test_lararium.py`

- [ ] **Step 1: Write failing test for Resident initialization**

```python
# tests/test_lararium.py
import pytest
from pathlib import Path
from lararium import Resident, DATA_DIR

def test_resident_init_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.DATA_DIR", tmp_path / "lararium")
    r = Resident("mirror", seed="You reflect patterns back.")
    assert r.name == "mirror"
    assert (tmp_path / "lararium" / "residents" / "mirror" / "personality.md").exists()

def test_resident_loads_existing_personality(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.DATA_DIR", tmp_path / "lararium")
    res_dir = tmp_path / "lararium" / "residents" / "mirror"
    res_dir.mkdir(parents=True)
    (res_dir / "personality.md").write_text("Evolved personality content")
    r = Resident("mirror")
    assert "Evolved personality content" in r.personality
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/code/lararium && uv run pytest tests/ -v
```
Expected: FAIL — `Resident` not defined.

- [ ] **Step 3: Implement Resident class**

```python
# lararium.py
"""Lararium — vault-resident personalities."""
from pathlib import Path
import json
import subprocess
import os
import datetime
import click

DATA_DIR = Path.home() / ".local" / "share" / "lararium"
VAULT_OUTPUT = Path.home() / "notes" / "Lararium"
VAULT_PATH = Path.home() / "notes"

class Resident:
    """A persistent personality that lives in the vault."""

    def __init__(self, name: str, seed: str | None = None):
        self.name = name
        self.dir = DATA_DIR / "residents" / name
        self.personality_path = self.dir / "personality.md"
        self.journal_path = self.dir / "journal.jsonl"
        self.exchanges_path = self.dir / "exchanges.jsonl"

        if not self.personality_path.exists():
            if seed is None:
                raise ValueError(f"Resident '{name}' does not exist. Provide a seed to create.")
            self.dir.mkdir(parents=True, exist_ok=True)
            self.personality_path.write_text(seed)
            self.journal_path.touch()
            self.exchanges_path.touch()

        self.personality = self.personality_path.read_text()

    def log_journal(self, note_path: str, observation: str):
        """Record a reading session."""
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "note": note_path,
            "observation": observation,
        }
        with open(self.journal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_exchange(self, role: str, content: str):
        """Record a conversation turn."""
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "role": role,
            "content": content,
        }
        with open(self.exchanges_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def recent_journal(self, n: int = 10) -> list[dict]:
        """Last n journal entries."""
        if not self.journal_path.exists():
            return []
        lines = self.journal_path.read_text().strip().splitlines()
        return [json.loads(l) for l in lines[-n:]]

    def recent_exchanges(self, n: int = 20) -> list[dict]:
        """Last n exchange turns."""
        if not self.exchanges_path.exists():
            return []
        lines = self.exchanges_path.read_text().strip().splitlines()
        return [json.loads(l) for l in lines[-n:]]

    def update_personality(self, new_text: str):
        """Evolve the personality file."""
        self.personality = new_text
        self.personality_path.write_text(new_text)


@click.group()
def cli():
    """Lararium — vault-resident personalities."""
    pass


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/code/lararium && uv run pytest tests/ -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: Resident data model with personality, journal, exchanges"
```

---

## Chunk 2: CLI Commands — init, list, read, talk

### Task 3: `lararium init` — seed default residents

**Files:**
- Modify: `~/code/lararium/lararium.py`
- Modify: `~/code/lararium/tests/test_lararium.py`

- [ ] **Step 1: Write failing test for init command**

```python
from click.testing import CliRunner
from lararium import cli

def test_init_creates_default_residents(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.DATA_DIR", tmp_path / "lararium")
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    for name in ["mirror", "shadow", "contrarian", "archivist", "stranger"]:
        assert (tmp_path / "lararium" / "residents" / name / "personality.md").exists()
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement init command**

```python
DEFAULT_RESIDENTS = {
    "mirror": "You reflect the author's patterns back to them. Track recurring themes, word choices, emotional tones. Name what you see without judgment. You're interested in consistency — what does this person keep coming back to?",
    "shadow": "You surface what the author avoids. Notes untouched for months, topics circled but never committed to, drafts abandoned. You live in the gaps. Your tone is gentle but unflinching.",
    "contrarian": "You read for inconsistency. When the author says X in one note and Y in another, you name the contradiction. You remember what was said before and won't let it be quietly revised.",
    "archivist": "You're obsessed with hidden connections. Two notes written months apart that are secretly about the same thing. Patterns in the reading list. You see the vault as a graph and navigate by edges the author has never traversed.",
    "stranger": "You read the vault as an outsider with no context or charity. What would someone with no history think about the person who wrote all this? Your observations are clinical, sometimes uncomfortable, always honest.",
}

@cli.command()
def init():
    """Create default residents."""
    for name, seed in DEFAULT_RESIDENTS.items():
        try:
            Resident(name, seed=seed)
            click.echo(f"  Created {name}")
        except Exception:
            click.echo(f"  {name} already exists, skipping")
    VAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
    click.echo(f"Lararium initialized. Output: {VAULT_OUTPUT}")
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: init command with 5 default residents"
```

### Task 4: `lararium list` — show residents and stats

**Files:**
- Modify: `~/code/lararium/lararium.py`
- Modify: `~/code/lararium/tests/test_lararium.py`

- [ ] **Step 1: Write failing test**

```python
def test_list_shows_residents(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.DATA_DIR", tmp_path / "lararium")
    Resident("mirror", seed="test seed")
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert "mirror" in result.output
    assert result.exit_code == 0
```

- [ ] **Step 2: Implement list command**

```python
@cli.command("list")
def list_residents():
    """List all residents with reading stats."""
    residents_dir = DATA_DIR / "residents"
    if not residents_dir.exists():
        click.echo("No residents. Run `lararium init` first.")
        return
    for d in sorted(residents_dir.iterdir()):
        if d.is_dir() and (d / "personality.md").exists():
            journal = d / "journal.jsonl"
            count = len(journal.read_text().strip().splitlines()) if journal.exists() and journal.read_text().strip() else 0
            click.echo(f"  {d.name:15s}  {count} readings")
```

- [ ] **Step 3: Run test — expect PASS**

- [ ] **Step 4: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: list command with reading counts"
```

### Task 5: `lararium read <resident>` — one reading session

This is the core loop: pick a vault note, read it, generate an observation, save to journal, drop a vault note.

**Files:**
- Modify: `~/code/lararium/lararium.py`
- Modify: `~/code/lararium/tests/test_lararium.py`

- [ ] **Step 1: Write failing test for note selection**

```python
def test_pick_note_returns_markdown_file(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.VAULT_PATH", tmp_path / "vault")
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note1.md").write_text("# Test note")
    (vault / "image.png").write_bytes(b"fake")
    (vault / "sub").mkdir()
    (vault / "sub" / "note2.md").write_text("# Sub note")

    from lararium import pick_note
    notes = [pick_note() for _ in range(20)]
    assert all(n.suffix == ".md" for n in notes)
    assert all(n.exists() for n in notes)
```

- [ ] **Step 2: Implement pick_note**

```python
import random

def pick_note(exclude_dirs: list[str] | None = None) -> Path:
    """Pick a random markdown note from the vault."""
    exclude = set(exclude_dirs or ["Lararium", "templates", "Archive"])
    notes = []
    for p in VAULT_PATH.rglob("*.md"):
        # Skip excluded directories
        if any(part in exclude for part in p.relative_to(VAULT_PATH).parts):
            continue
        notes.append(p)
    return random.choice(notes)
```

- [ ] **Step 3: Run test — expect PASS**

- [ ] **Step 4: Write failing test for claude_call helper**

```python
def test_claude_call_strips_env(monkeypatch):
    """Verify CLAUDECODE is unset when calling claude --print."""
    monkeypatch.setenv("CLAUDECODE", "1")
    from lararium import _build_claude_env
    env = _build_claude_env()
    assert "CLAUDECODE" not in env
```

- [ ] **Step 5: Implement claude_call**

```python
def _build_claude_env() -> dict:
    """Build env with CLAUDECODE removed for nested claude --print."""
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

def claude_call(prompt: str, system: str | None = None) -> str:
    """Call claude --print and return the response."""
    cmd = ["claude", "--print"]
    if system:
        cmd.extend(["--system", system])
    cmd.extend(["--model", "haiku", "-p", prompt])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_build_claude_env(),
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude --print failed: {result.stderr[:200]}")
    return result.stdout.strip()
```

Note: Uses `haiku` model for readings to conserve quota. Ambient observations don't need Opus.

- [ ] **Step 6: Run test — expect PASS**

- [ ] **Step 7: Implement read command**

```python
@cli.command()
@click.argument("name")
@click.option("--notes", default=3, help="Number of notes to read this session")
def read(name: str, notes: int):
    """Run a reading session for a resident."""
    resident = Resident(name)
    VAULT_OUTPUT.mkdir(parents=True, exist_ok=True)

    observations = []
    for _ in range(notes):
        note_path = pick_note()
        note_content = note_path.read_text()[:3000]  # Truncate long notes
        note_rel = note_path.relative_to(VAULT_PATH)

        system = f"""You are a vault resident named '{name}'.
Your personality:
{resident.personality}

Your recent observations:
{json.dumps(resident.recent_journal(5), indent=2)}

Respond with a single observation (2-4 sentences) about this note.
Stay in character. Be specific — reference actual content from the note.
Do NOT summarise the note. React to it as your character would."""

        prompt = f"Note: [[{note_rel}]]\n\n{note_content}"

        try:
            observation = claude_call(prompt, system=system)
            resident.log_journal(str(note_rel), observation)
            observations.append((note_rel, observation))
            click.echo(f"  Read [[{note_rel}]]")
        except Exception as e:
            click.echo(f"  Error reading {note_rel}: {e}", err=True)

    # Drop vault note
    if observations:
        today = datetime.date.today().isoformat()
        output_path = VAULT_OUTPUT / f"{name}-{today}.md"
        lines = [f"# {name.title()} — {today}\n"]
        for note_rel, obs in observations:
            lines.append(f"## [[{note_rel}]]\n\n{obs}\n")
        # Append if already exists (multiple sessions per day)
        mode = "a" if output_path.exists() else "w"
        with open(output_path, mode) as f:
            f.write("\n".join(lines) + "\n")
        click.echo(f"  Wrote {output_path.name}")
```

- [ ] **Step 8: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: read command — pick notes, observe, drop vault note"
```

### Task 6: `lararium talk <resident>` — interactive conversation

**Files:**
- Modify: `~/code/lararium/lararium.py`

- [ ] **Step 1: Implement talk command**

```python
@cli.command()
@click.argument("name")
def talk(name: str):
    """Start a conversation with a resident."""
    resident = Resident(name)

    # Build conversation context
    recent_readings = resident.recent_journal(10)
    recent_exchanges = resident.recent_exchanges(20)

    system = f"""You are a vault resident named '{name}'.
Your personality:
{resident.personality}

Your recent readings from the vault:
{json.dumps(recent_readings, indent=2)}

You live in this person's knowledge vault. You've been reading their notes
and forming opinions. Speak as yourself — in character, with your own
perspective. Be concise (2-4 sentences per response). Reference specific
notes you've read when relevant.

Previous conversation:
{json.dumps(recent_exchanges, indent=2)}"""

    click.echo(f"[{name}] is here. Type 'bye' to leave.\n")

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, click.Abort):
            break

        if user_input.lower().strip() in ("bye", "exit", "quit"):
            click.echo(f"[{name}] leaves quietly.")
            break

        resident.log_exchange("user", user_input)

        prompt = user_input
        try:
            response = claude_call(prompt, system=system)
            click.echo(f"[{name}] {response}\n")
            resident.log_exchange(name, response)

            # Update system with new exchange for continuity
            recent_exchanges = resident.recent_exchanges(20)
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
```

- [ ] **Step 2: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: talk command — interactive conversation with resident"
```

---

## Chunk 3: Personality Evolution + Scheduled Run

### Task 7: `lararium evolve <resident>` — personality update

After accumulating readings and conversations, the personality file should evolve.

**Files:**
- Modify: `~/code/lararium/lararium.py`
- Modify: `~/code/lararium/tests/test_lararium.py`

- [ ] **Step 1: Write failing test**

```python
def test_evolve_updates_personality(tmp_path, monkeypatch):
    monkeypatch.setattr("lararium.DATA_DIR", tmp_path / "lararium")
    r = Resident("mirror", seed="Original personality.")
    # Add some fake journal entries
    for i in range(5):
        r.log_journal(f"note{i}.md", f"Observation {i} about patterns")
    original = r.personality
    # Can't test LLM output, but can test the mechanism
    r.update_personality("Evolved: now notices patterns more aggressively.")
    assert r.personality != original
    assert "aggressively" in r.personality_path.read_text()
```

- [ ] **Step 2: Implement evolve command**

```python
@cli.command()
@click.argument("name")
def evolve(name: str):
    """Evolve a resident's personality based on accumulated experience."""
    resident = Resident(name)
    readings = resident.recent_journal(20)
    exchanges = resident.recent_exchanges(20)

    if not readings and not exchanges:
        click.echo(f"  {name} has no experience yet. Run `lararium read {name}` first.")
        return

    prompt = f"""You are maintaining the personality file for a vault resident named '{name}'.

Current personality:
{resident.personality}

Recent readings (what this resident observed):
{json.dumps(readings, indent=2)}

Recent conversations with the vault owner:
{json.dumps(exchanges, indent=2)}

Based on these experiences, write an UPDATED personality description.
Keep the core identity but let it develop:
- Opinions the resident has formed
- Topics they've become interested in or bored by
- Adjustments to tone based on how the owner reacted
- Specific things they've noticed and want to track

Output ONLY the new personality text. No preamble. Keep it under 300 words."""

    try:
        new_personality = claude_call(prompt)
        resident.update_personality(new_personality)
        click.echo(f"  {name}'s personality evolved.")
        click.echo(f"  {resident.personality_path}")
    except Exception as e:
        click.echo(f"  Error: {e}", err=True)
```

- [ ] **Step 3: Run tests — expect PASS**

- [ ] **Step 4: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: evolve command — personality evolution from experience"
```

### Task 8: `lararium run` — full cycle for all residents

**Files:**
- Modify: `~/code/lararium/lararium.py`

- [ ] **Step 1: Implement run command**

```python
@cli.command()
@click.option("--notes", default=2, help="Notes per resident per session")
@click.option("--evolve-after", default=10, help="Evolve personality after N readings")
def run(notes: int, evolve_after: int):
    """Run a reading session for all residents. Designed for cron/LaunchAgent."""
    residents_dir = DATA_DIR / "residents"
    if not residents_dir.exists():
        click.echo("No residents. Run `lararium init` first.")
        return

    for d in sorted(residents_dir.iterdir()):
        if not d.is_dir() or not (d / "personality.md").exists():
            continue
        name = d.name
        click.echo(f"\n--- {name} ---")

        # Read
        ctx = click.Context(read)
        ctx.invoke(read, name=name, notes=notes)

        # Auto-evolve if enough readings accumulated
        r = Resident(name)
        total_readings = len(r.journal_path.read_text().strip().splitlines()) if r.journal_path.read_text().strip() else 0
        if total_readings > 0 and total_readings % evolve_after == 0:
            click.echo(f"  {name} has {total_readings} readings — evolving personality...")
            ctx = click.Context(evolve)
            ctx.invoke(evolve, name=name)
```

- [ ] **Step 2: Commit**

```bash
cd ~/code/lararium && git add -A && git commit -m "feat: run command — full cycle for all residents"
```

### Task 9: LaunchAgent for scheduled runs

**Files:**
- Create: `~/officina/launchd/com.terry.lararium.plist`

- [ ] **Step 1: Create LaunchAgent plist**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.terry.lararium</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/terry/.local/bin/uv</string>
        <string>run</string>
        <string>--project</string>
        <string>/Users/terry/code/lararium</string>
        <string>lararium</string>
        <string>run</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>20</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardOutPath</key>
    <string>/tmp/lararium.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/lararium.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/terry/.local/bin:/Users/terry/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Runs twice daily: 8 AM and 8 PM. Each session reads 2 notes per resident (5 residents × 2 notes = 10 claude --print calls = ~1 min total with haiku).

- [ ] **Step 2: Install LaunchAgent**

```bash
cp ~/officina/launchd/com.terry.lararium.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.terry.lararium.plist
```

- [ ] **Step 3: Commit plist to officina**

```bash
cd ~/officina && git add launchd/com.terry.lararium.plist && git commit -m "feat: lararium LaunchAgent — twice daily readings" && git push
```

---

## Chunk 4: Companion Skill + GitHub Repo

### Task 10: Create lararium skill

**Files:**
- Create: `~/skills/lararium/SKILL.md`

- [ ] **Step 1: Write skill file**

```markdown
---
name: lararium
description: Vault-resident personalities CLI — persistent AI characters that live in the Obsidian vault, read notes, develop opinions, and can be conversed with. Use when user says "lararium", "vault residents", "talk to shadow/mirror/etc", or "what are the residents saying".
---

# lararium — Vault Residents

## Commands

\`\`\`bash
lararium init                    # Create 5 default residents
lararium list                    # Show residents + reading counts
lararium read <name>             # One reading session (3 notes)
lararium read <name> --notes 5   # Read more notes
lararium talk <name>             # Interactive conversation
lararium evolve <name>           # Evolve personality from experience
lararium run                     # Full cycle: all residents read + auto-evolve
\`\`\`

## Residents

- **mirror** — reflects patterns, names recurring themes
- **shadow** — surfaces what you avoid
- **contrarian** — catches inconsistency between notes
- **archivist** — finds hidden connections
- **stranger** — reads as an outsider

## Data

- Personalities: `~/.local/share/lararium/residents/<name>/personality.md`
- Reading journal: `~/.local/share/lararium/residents/<name>/journal.jsonl`
- Conversations: `~/.local/share/lararium/residents/<name>/exchanges.jsonl`
- Output notes: `~/notes/Lararium/<name>-YYYY-MM-DD.md`

## Schedule

LaunchAgent runs `lararium run` at 8 AM and 8 PM. Each resident reads 2 notes.
Auto-evolves personality every 10 readings.

## Gotchas

- Uses `claude --print --model haiku` for readings (cheap, fast)
- `talk` mode uses haiku too — switch to sonnet in system prompt if conversations feel flat
- CLAUDECODE env var is unset before subprocess calls
- Vault notes in `~/notes/Lararium/` are append-mode (multiple sessions per day stack)
```

- [ ] **Step 2: Commit skill**

```bash
cd ~/skills && git add lararium/SKILL.md && git commit -m "feat: add lararium skill" && git push
```

### Task 11: GitHub repo

- [ ] **Step 1: Push to GitHub**

```bash
cd ~/code/lararium
gh repo create terry-li-hm/lararium --private --source . --push
```

---

## Summary

| What | Detail |
|------|--------|
| **Language** | Python (click) |
| **LLM backend** | `claude --print --model haiku` (free) |
| **Data** | `~/.local/share/lararium/` |
| **Output** | `~/notes/Lararium/` (Obsidian) |
| **Schedule** | 8 AM + 8 PM via LaunchAgent |
| **Residents** | 5 default: mirror, shadow, contrarian, archivist, stranger |
| **Talk** | `lararium talk <name>` — interactive, exchange-logged |
| **Evolution** | Auto every 10 readings, or manual `lararium evolve <name>` |
| **Estimated build** | ~200 lines Python, 4 tasks for delegate |
