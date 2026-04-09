#!/usr/bin/env bash
# harness-setup.sh — deterministic setup for all ribosome harnesses on any worker.
# Run once after provisioning, or anytime config drifts.
# Requires: ZHIPU_API_KEY in env (via op run or direct).
# LOCKED: this is the single source of truth for harness config on workers.
set -euo pipefail

echo "==> Harness setup (all 4)"

# Validate prereqs
for bin in claude goose droid; do
  if ! command -v "$bin" &>/dev/null; then
    echo "WARN: $bin not found on PATH" >&2
  fi
done
if [[ ! -x "$HOME/.opencode/bin/opencode" ]]; then
  echo "WARN: opencode not found at ~/.opencode/bin/opencode" >&2
fi

# 1. Claude Code — needs hasCompletedOnboarding only (env vars set at runtime by ribosome)
mkdir -p "$HOME/.claude"
cat > "$HOME/.claude.json" <<'CLAUDE_JSON'
{
  "hasCompletedOnboarding": true
}
CLAUDE_JSON
echo "  [claude] .claude.json written"

# 2. OpenCode — custom provider + permissions
mkdir -p "$HOME/.config/opencode" "$HOME/.local/share/opencode"

cat > "$HOME/.config/opencode/opencode.json" <<'OC_CONFIG'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "zhipu-coding": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://open.bigmodel.cn/api/coding/paas/v4",
        "apiKey": "{env:ZHIPU_API_KEY}"
      },
      "models": { "glm-5.1": { "name": "GLM-5.1" } }
    }
  },
  "permission": { "*": "allow", "external_directory": { "*": "allow" } }
}
OC_CONFIG
echo "  [opencode] config written"

# OpenCode auth.json — write from env if available
if [[ -n "${ZHIPU_API_KEY:-}" ]]; then
  printf '{"zhipuai":{"apiKey":"%s"}}' "$ZHIPU_API_KEY" > "$HOME/.local/share/opencode/auth.json"
  echo "  [opencode] auth.json written from ZHIPU_API_KEY"
else
  echo "  [opencode] ZHIPU_API_KEY not set — auth.json skipped (ribosome injects at runtime)"
fi

# OpenCode on PATH
if [[ -x "$HOME/.opencode/bin/opencode" ]] && ! command -v opencode &>/dev/null; then
  mkdir -p "$HOME/bin"
  ln -sf "$HOME/.opencode/bin/opencode" "$HOME/bin/opencode"
  echo "  [opencode] symlinked to ~/bin/opencode"
fi

# 3. Goose — no persistent config needed (env vars at runtime)
echo "  [goose] no config needed (env vars at runtime)"

# 4. Droid — no persistent config needed (env vars at runtime)
echo "  [droid] no config needed (env vars at runtime)"

echo "==> Done. All harness configs locked."
