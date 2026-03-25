#!/bin/bash
# Guard against OpenClaw WhatsApp being enabled or dmPolicy being set to "pairing"
# WhatsApp plugin should stay DISABLED to prevent prompt injection risks
# wacli still works independently for reading messages

CONFIG_FILE="$HOME/.openclaw/openclaw.json"
LOG_FILE="$HOME/.openclaw/logs/whatsapp-guard.log"

if [ ! -f "$CONFIG_FILE" ]; then
    exit 0
fi

NEEDS_FIX=false

# Check if WhatsApp plugin is enabled (should be false)
WA_ENABLED=$(jq -r '.plugins.entries.whatsapp.enabled // true' "$CONFIG_FILE" 2>/dev/null)
if [ "$WA_ENABLED" = "true" ]; then
    echo "$(date): ALERT - WhatsApp plugin enabled, disabling..." >> "$LOG_FILE"
    jq '.plugins.entries.whatsapp.enabled = false' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    NEEDS_FIX=true
fi

# Also check dmPolicy as backup (in case plugin gets re-enabled)
WA_POLICY=$(jq -r '.channels.whatsapp.dmPolicy // empty' "$CONFIG_FILE" 2>/dev/null)
if [ "$WA_POLICY" = "pairing" ]; then
    echo "$(date): ALERT - dmPolicy=pairing found, fixing..." >> "$LOG_FILE"
    jq '.channels.whatsapp.dmPolicy = "allowlist" | .channels.whatsapp.accounts.default.dmPolicy = "allowlist"' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    NEEDS_FIX=true
fi

if [ "$NEEDS_FIX" = true ]; then
    openclaw gateway restart 2>/dev/null
    echo "$(date): Gateway restarted" >> "$LOG_FILE"
fi
