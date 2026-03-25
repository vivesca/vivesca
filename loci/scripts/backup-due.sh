#!/bin/bash
# Backup Due.duedb to reticulum with git commit for changelog
DUEDB="$HOME/Library/Containers/com.phocusllp.duemac/Data/Library/Application Support/Due App/Due.duedb"
DEST="$HOME/reticulum/due-backup/Due.duedb"

mkdir -p "$HOME/reticulum/due-backup"
cp "$DUEDB" "$DEST"

python3 "$HOME/reticulum/scripts/export-due.py"

cd "$HOME/reticulum"
git add due-backup/Due.duedb due-backup/reminders.md
git diff --cached --quiet || git commit -m "chore: Due.duedb backup $(date '+%Y-%m-%d %H:%M')"
