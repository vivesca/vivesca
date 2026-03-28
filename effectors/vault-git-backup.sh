#!/bin/bash
# Vault git backup — auto-commit and push if there are changes
# Replaces Obsidian Git plugin (which only runs when app is open)

cd "$HOME/epigenome/chromatin" || exit 1

# Pull remote changes first (Obsidian Git may have pushed)
git fetch origin main 2>/dev/null
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

# Skip if no changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    exit 0
fi

git add -A
git commit -m "vault backup: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
