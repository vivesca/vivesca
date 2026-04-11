---
name: deleo
description: Safe deletion CLI — validates paths and performs deletion with confirmation. Use when deleting files or directories safely. "delete", "remove", "safe delete"
effort: low
---

# deleo

Latin: *to destroy/delete* — the etymological root of "delete".

Rust CLI that validates protected paths, shows what will be deleted, prompts for confirmation, then performs the actual deletion.

Replaces the old two-step: `python3 ~/scripts/safe_rm.py <path>` + manual `rm`.

## Installation

```bash
cd ~/code/deleo && cargo build --release
ln -sf ~/code/deleo/target/release/deleo ~/bin/deleo
```

## Commands

```bash
# Interactive delete (shows size, prompts y/N)
deleo ~/some/path

# Multiple paths — validates all before prompting
deleo ~/path/a ~/path/b

# Skip confirmation (for hooks/scripts)
deleo --force ~/path

# Dry run — validate and report, no delete
deleo --dry-run ~/path
deleo -n ~/path
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Deleted, dry-run OK, or user aborted |
| 1 | Protected path blocked |
| 2 | IO error during deletion |

## Protected Paths

Refuses to delete (exit 1):
- `/`, `/Users`, `/Users/terry`, `~`
- `~/.ssh`, `~/.gnupg`
- `/etc`, `/usr`, `/System`, `/bin`, `/sbin`, `/var`, `/tmp`

Also blocks deletion of any parent of a protected path.

## Hook Integration

CLAUDE.md: `rm -rf` → `deleo <path>` (replaces `python3 ~/scripts/safe_rm.py <path>`)

Use `--force` in scripts after validation. Interactive use: let it prompt.

## Source

`~/code/deleo/` — Rust, clap 4, release profile with strip=true.
