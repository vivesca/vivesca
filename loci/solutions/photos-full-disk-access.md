# Photos.app Full Disk Access for Claude Code

## Problem

`photos.py` (direct SQLite on Photos Library) fails with `sqlite3.OperationalError: unable to open database file`. macOS TCC blocks access without Full Disk Access.

## Root Cause

TCC checks the **responsible process**, not the script itself:

- **Blink/SSH sessions:** responsible process = `/usr/sbin/sshd`
- **Local Ghostty:** responsible process = `Ghostty.app`
- **tmux doesn't matter** — it inherits from whatever launched it

## Fix

System Settings → Privacy & Security → Full Disk Access → add:

- `/usr/sbin/sshd` (for SSH/Blink sessions)
- `Ghostty.app` in `/Applications/` (for local sessions)

**Restart required:** SSH needs a new connection (tmux survives). Ghostty needs a new window or app restart.

## Security Note

Granting FDA to `sshd` means any SSH session gets full disk access. Acceptable for single-user machines.
