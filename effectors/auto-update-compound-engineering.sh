#!/usr/bin/env bash
# Auto-update compound-engineering plugin
# Add to crontab: 0 2 * * 0 ~/germline/effectors/auto-update-compound-engineering.sh

LOG_FILE="$HOME/.compound-engineering-updates.log"

echo "========================================" >> "$LOG_FILE"
echo "Update started: $(date)" >> "$LOG_FILE"

# Update OpenCode
echo "Updating OpenCode..." >> "$LOG_FILE"
if bunx @every-env/compound-plugin install compound-engineering --to opencode >> "$LOG_FILE" 2>&1; then
    echo "✅ OpenCode updated successfully" >> "$LOG_FILE"
else
    echo "❌ OpenCode update failed" >> "$LOG_FILE"
fi

# Update Codex
echo "Updating Codex..." >> "$LOG_FILE"
if bunx @every-env/compound-plugin install compound-engineering --to codex >> "$LOG_FILE" 2>&1; then
    echo "✅ Codex updated successfully" >> "$LOG_FILE"
else
    echo "❌ Codex update failed" >> "$LOG_FILE"
fi

echo "Update completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
