#!/usr/bin/env bash
set -euo pipefail
# Chromatin git backup — auto-commit and push if there are changes
# Replaces Obsidian Git plugin (which only runs when app is open)

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: chromatin-backup.sh"
    echo
    echo "Auto-commit and push chromatin changes to epigenome repo."
    echo "Skips if no changes detected."
    exit 0
fi

cd "$HOME/epigenome/chromatin" || exit 1

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    exit 0
fi

# 1. Commit any local changes first
if ! (git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]); then
    git add -A
    git commit -m "chromatin backup: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 2. Sync with remote
git fetch origin main 2>/dev/null || true

if git rev-parse --verify origin/main >/dev/null 2>&1; then
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
        # Rebase local changes on top of remote, auto-resolve conflicts by keeping both
        GIT_EDITOR="true" git rebase origin/main 2>/dev/null || {
            # If rebase fails (conflict), abort and merge instead
            git rebase --abort 2>/dev/null
            git merge origin/main --no-edit 2>/dev/null || {
                # Last resort: accept theirs for auto-backup conflicts
                git checkout --theirs . 2>/dev/null
                git add -A
                GIT_EDITOR="true" git commit --no-edit 2>/dev/null
            }
        }
    fi
fi

# 3. Push if we are ahead of origin/main
if git rev-parse --verify origin/main >/dev/null 2>&1; then
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
        git push origin main
    fi
fi
