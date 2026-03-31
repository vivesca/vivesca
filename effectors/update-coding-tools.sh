#!/usr/bin/env bash
# Auto-update all tools hourly
# Runs via LaunchAgent com.terry.update-coding-tools

set -e

# Cron runs with minimal PATH — load Homebrew and user binaries
eval "$(/opt/homebrew/bin/brew shellenv)"
export PATH="$HOME/.cargo/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$HOME/Library/pnpm:$PATH"

LOG_FILE="$HOME/.coding-tools-update.log"
echo "=== $(date) ===" >> "$LOG_FILE"

# ── Homebrew (everything) ──
echo "Updating brew..." | tee -a "$LOG_FILE"
brew update 2>&1 | tee -a "$LOG_FILE" || true
brew upgrade 2>&1 | tee -a "$LOG_FILE" || true
brew upgrade --cask --greedy 2>&1 | tee -a "$LOG_FILE" || true
brew cleanup --prune=7 2>&1 | tee -a "$LOG_FILE" || true

# ── npm globals ──
echo "Updating npm globals..." | tee -a "$LOG_FILE"
npm update -g 2>&1 | tee -a "$LOG_FILE" || true

# ── pnpm globals ──
echo "Updating pnpm globals..." | tee -a "$LOG_FILE"
pnpm update -g 2>&1 | tee -a "$LOG_FILE" || true

# ── uv tools ──
echo "Updating uv tools..." | tee -a "$LOG_FILE"
uv tool upgrade --all 2>&1 | tee -a "$LOG_FILE" || true

# ── Cargo tools ──
echo "Updating cargo tools..." | tee -a "$LOG_FILE"
cargo binstall -y compound-perplexity typos-cli 2>&1 | tee -a "$LOG_FILE" || true

# ── Mac App Store ──
echo "Updating Mac App Store apps..." | tee -a "$LOG_FILE"
mas upgrade 2>&1 | tee -a "$LOG_FILE" || true

# ── Post-update self-heal ──
echo "Verifying critical tools..." | tee -a "$LOG_FILE"
HEALTH_FILE="$HOME/.coding-tools-health.json"

declare -A REPAIR=(
  [brew]="/opt/homebrew/bin/brew"
  [claude]="brew install --cask claude"
  [opencode]="brew install opencode"
  [gemini]="brew install gemini-cli"
  [codex]="brew install codex"
  [agent-browser]="brew install agent-browser"
  [mas]="brew install mas"
)

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
