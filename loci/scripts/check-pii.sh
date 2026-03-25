#!/usr/bin/env bash
# Pre-commit hook: reject commits containing personal data patterns.
# Reads patterns from ~/.config/vivesca/pii-patterns.txt (one regex per line).
# Preventive control against PII leaking into public repo history.
# Uses git diff --cached to search staged content (avoids shell grep guards).

set -euo pipefail

PATTERNS_FILE="${VIVESCA_PII_PATTERNS:-$HOME/.config/vivesca/pii-patterns.txt}"

if [ ! -f "$PATTERNS_FILE" ]; then
    exit 0  # No patterns file = no check (generic installs skip this)
fi

ERRORS=0

while IFS= read -r pattern; do
    [[ "$pattern" =~ ^#.*$ || -z "$pattern" ]] && continue

    # Search staged diff content, not files on disk
    if git diff --cached -U0 | grep -qP "$pattern" 2>/dev/null; then
        echo "PII pattern detected: $pattern"
        ERRORS=$((ERRORS + 1))
    fi
done < "$PATTERNS_FILE"

if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "Blocked: $ERRORS PII pattern(s) found in staged changes."
    echo "Edit ~/.config/vivesca/pii-patterns.txt to manage patterns."
    exit 1
fi
