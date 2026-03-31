#!/bin/bash
# backup-due.sh — nightly backup of Due app database
# Copies Due's Compact.duecdb to ~/epigenome/oscillators/backups/ with a datestamp.
# Runs nightly at 23:00 via com.terry.due-backup LaunchAgent.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: backup-due.sh"
    echo ""
    echo "Nightly backup of Due app database (macOS)."
    echo "Copies Due's Compact.duecdb to ~/epigenome/oscillators/backups/ with a datestamp."
    echo "Retains the last 30 backups. Run via com.terry.due-backup LaunchAgent."
    exit 0
fi

DUE_DB="$HOME/Library/Group Containers/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb"
BACKUP_DIR="$HOME/epigenome/oscillators/backups"
TIMESTAMP=$(date '+%Y-%m-%d')
DEST="$BACKUP_DIR/due-$TIMESTAMP.duecdb"

if [ ! -f "$DUE_DB" ]; then
    echo "ERROR: Due database not found at $DUE_DB" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
cp "$DUE_DB" "$DEST"
echo "due-backup: copied $(basename "$DUE_DB") -> $DEST"

# Keep only the last 30 backups
ls -t "$BACKUP_DIR"/due-*.duecdb 2>/dev/null | tail -n +31 | xargs rm -f --
echo "due-backup: retention pruned, $(ls "$BACKUP_DIR"/due-*.duecdb 2>/dev/null | wc -l | tr -d ' ') backups retained"
