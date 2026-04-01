#!/usr/bin/env bash
# Auto-update all tools hourly
# macOS: LaunchAgent com.terry.update-coding-tools
# Linux: systemd timer or cron

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: update-coding-tools.sh"
    echo
    echo "Auto-update brew (macOS) / apt (Linux), npm, pnpm, uv, and cargo tools."
    echo "Logs to ~/.coding-tools-update.log."
    exit 0
fi

set -e

export PATH="$HOME/.cargo/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$HOME/Library/pnpm:$PATH"

LOG_FILE="$HOME/.coding-tools-update.log"
echo "=== $(date) ===" >> "$LOG_FILE"

OS="$(uname -s)"

# ── System packages ──
if [[ "$OS" == "Darwin" ]]; then
    if command -v brew &>/dev/null; then
        eval "$(brew shellenv)"
        echo "Updating brew..." | tee -a "$LOG_FILE"
        brew update 2>&1 | tee -a "$LOG_FILE" || true
        brew upgrade 2>&1 | tee -a "$LOG_FILE" || true
        brew upgrade --cask --greedy 2>&1 | tee -a "$LOG_FILE" || true
        brew cleanup --prune=7 2>&1 | tee -a "$LOG_FILE" || true
    else
        echo "Warning: Homebrew not found on macOS." | tee -a "$LOG_FILE"
    fi
    # Mac App Store
    if command -v mas &>/dev/null; then
        echo "Updating Mac App Store apps..." | tee -a "$LOG_FILE"
        mas upgrade 2>&1 | tee -a "$LOG_FILE" || true
    fi
elif [[ "$OS" == "Linux" ]]; then
    if command -v apt &>/dev/null; then
        echo "Updating apt packages..." | tee -a "$LOG_FILE"
        sudo apt update 2>&1 | tee -a "$LOG_FILE" || true
        sudo apt upgrade -y 2>&1 | tee -a "$LOG_FILE" || true
        sudo apt autoremove -y 2>&1 | tee -a "$LOG_FILE" || true
    fi
fi

# ── npm globals ──
if command -v npm &>/dev/null; then
    echo "Updating npm globals..." | tee -a "$LOG_FILE"
    npm update -g 2>&1 | tee -a "$LOG_FILE" || true
fi

# ── pnpm globals ──
if command -v pnpm &>/dev/null; then
    echo "Updating pnpm globals..." | tee -a "$LOG_FILE"
    pnpm update -g 2>&1 | tee -a "$LOG_FILE" || true
fi

# ── uv tools ──
if command -v uv &>/dev/null; then
    echo "Updating uv tools..." | tee -a "$LOG_FILE"
    uv tool upgrade --all 2>&1 | tee -a "$LOG_FILE" || true
fi

# ── Cargo tools ──
if command -v cargo &>/dev/null; then
    echo "Updating cargo tools..." | tee -a "$LOG_FILE"
    cargo binstall -y compound-perplexity typos-cli 2>&1 | tee -a "$LOG_FILE" || true
fi

# ── Post-update self-heal ──
echo "Verifying critical tools..." | tee -a "$LOG_FILE"
HEALTH_FILE="$HOME/.coding-tools-health.json"

declare -A REPAIR=()
if [[ "$OS" == "Darwin" ]]; then
    REPAIR=(
      [brew]="/opt/homebrew/bin/brew"
      [claude]="brew install --cask claude"
      [opencode]="brew install opencode"
      [gemini]="brew install gemini-cli"
      [codex]="brew install codex"
      [agent-browser]="brew install agent-browser"
      [mas]="brew install mas"
    )
else
    REPAIR=(
      [claude]="npm install -g @anthropic-ai/claude-code"
      [gemini]="npm install -g @anthropic-ai/gemini-cli"
    )
fi

failures=()
for cmd in "${!REPAIR[@]}"; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Repairing $cmd..." | tee -a "$LOG_FILE"
    eval "${REPAIR[$cmd]}" 2>&1 | tee -a "$LOG_FILE" || true
    if ! command -v "$cmd" &>/dev/null; then
      failures+=("$cmd")
    fi
  fi
done

if [ ${#failures[@]} -eq 0 ]; then
  echo '{"status":"ok","checked":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","failures":[]}' > "$HEALTH_FILE"
  echo "Health: ok" | tee -a "$LOG_FILE"
else
  fail_json=$(printf '"%s",' "${failures[@]}" | sed 's/,$//')
  echo '{"status":"degraded","checked":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","failures":['"$fail_json"']}' > "$HEALTH_FILE"
  echo "Health: DEGRADED — repair failed: ${failures[*]}" | tee -a "$LOG_FILE"
fi

echo "=== Updates complete $(date) ===" | tee -a "$LOG_FILE"
