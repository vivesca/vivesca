#!/usr/bin/env bash
# Auto-update compound-engineering plugin
# Add to crontab: 0 2 * * 0 ~/germline/effectors/auto-update-compound-engineering.sh

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: auto-update-compound-engineering.sh"
    echo ""
    echo "Run the compound-engineering plugin update for OpenCode and Codex."
    echo "Logs output to ~/.compound-engineering-updates.log"
    echo ""
    echo "Schedule via crontab:"
    echo "  0 2 * * 0 ~/germline/effectors/auto-update-compound-engineering.sh"
    exit 0
fi

LOG_FILE="$HOME/.compound-engineering-updates.log"

# Use bunx if available, fall back to npx
if command -v bunx &>/dev/null; then
    RUNNER=bunx
elif command -v npx &>/dev/null; then
    RUNNER=npx
else
    echo "Error: neither bunx nor npx found. Install bun or node." >> "$LOG_FILE"
    exit 1
fi

echo "========================================" >> "$LOG_FILE"
echo "Update started: $(date)" >> "$LOG_FILE"

# Update OpenCode
echo "Updating OpenCode..." >> "$LOG_FILE"
if $RUNNER @every-env/compound-plugin install compound-engineering --to opencode >> "$LOG_FILE" 2>&1; then
    echo "✅ OpenCode updated successfully" >> "$LOG_FILE"
else
    echo "❌ OpenCode update failed" >> "$LOG_FILE"
fi

# Update Codex
echo "Updating Codex..." >> "$LOG_FILE"
if $RUNNER @every-env/compound-plugin install compound-engineering --to codex >> "$LOG_FILE" 2>&1; then
    echo "✅ Codex updated successfully" >> "$LOG_FILE"
else
    echo "❌ Codex update failed" >> "$LOG_FILE"
fi

echo "Update completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
