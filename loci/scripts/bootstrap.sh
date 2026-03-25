#!/usr/bin/env bash
# Bootstrap a new machine for Claude Code agent workflow.
# Idempotent — safe to re-run.
#
# Usage:
#   bash <(ssh mac cat agent-config/scripts/bootstrap.sh)   # first run
#   ~/agent-config/scripts/bootstrap.sh                      # re-run
#   ~/agent-config/scripts/bootstrap.sh --nixos              # also prints nixos-rebuild command

set -uo pipefail

# ── Helpers ────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
DIM='\033[2m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { printf "${GREEN}✓${NC} %s\n" "$1"; }
skip() { printf "${DIM}· %s${NC}\n" "$1"; }
warn() { printf "${YELLOW}⚠ %s${NC}\n" "$1"; }

need() {
    if ! command -v "$1" &>/dev/null; then
        warn "Missing required command: $1 — install it first"
        return 1
    fi
}

NIXOS=false
[[ "${1:-}" == "--nixos" ]] && NIXOS=true

OS="$(uname)"
GH="https://github.com/terry-li-hm"

# Ensure tool install dirs are in PATH for idempotency checks
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/go/bin:$PATH"

# ── 1. Clone repos ────────────────────────────────────────────────────────

clone_or_pull() {
    local repo="$1" dir="$2"
    if [ -d "$dir/.git" ]; then
        (cd "$dir" && git pull -q 2>/dev/null) && skip "Pulled $dir"
    else
        git clone -q "$GH/$repo.git" "$dir" && ok "Cloned $dir"
    fi
}

echo ""
echo "=== Repos ==="

clone_or_pull dotfiles           "$HOME/dotfiles"
clone_or_pull agent-config       "$HOME/agent-config"
clone_or_pull skills             "$HOME/skills"
clone_or_pull notes              "$HOME/code/vivesca-terry/chromatin"
clone_or_pull scripts            "$HOME/scripts"
clone_or_pull compound-perplexity "$HOME/code/pplx"
clone_or_pull resurface          "$HOME/code/resurface"
clone_or_pull oghma              "$HOME/code/oghma"
clone_or_pull pharos             "$HOME/code/pharos"
clone_or_pull lustro             "$HOME/code/lustro"

# ── 2. Run setup scripts ──────────────────────────────────────────────────

echo ""
echo "=== Setup scripts ==="

if [ -f "$HOME/dotfiles/install.sh" ]; then
    bash "$HOME/dotfiles/install.sh"
    ok "Ran dotfiles/install.sh"
fi

if [ -f "$HOME/agent-config/scripts/setup-symlinks.sh" ]; then
    bash "$HOME/agent-config/scripts/setup-symlinks.sh"
    ok "Ran setup-symlinks.sh"
fi

# Skills symlink
if [ ! -L "$HOME/.claude/skills" ]; then
    mkdir -p "$HOME/.claude"
    ln -sf "$HOME/skills" "$HOME/.claude/skills"
    ok "Linked ~/.claude/skills → ~/skills"
else
    skip "Skills symlink already exists"
fi

# ~/bin symlink (setup-symlinks may handle this, but verify)
if [ ! -L "$HOME/bin" ]; then
    if [ -d "$HOME/agent-config/bin" ]; then
        ln -sf "$HOME/agent-config/bin" "$HOME/bin"
        ok "Linked ~/bin → ~/agent-config/bin"
    fi
else
    skip "~/bin symlink already exists"
fi

# ── 3. Install user-level tools ───────────────────────────────────────────

echo ""
echo "=== User tools ==="

# --- npm global tools (into ~/.local) ---

npm_install() {
    local pkg="$1" cmd="${2:-}"
    # Derive command name from package if not given
    [ -z "$cmd" ] && cmd="$(basename "$pkg" | sed 's/@.*//; s/.*\///')"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif need npm; then
        npm install -g --prefix "$HOME/.local" "$pkg" && ok "Installed $cmd (npm)"
    fi
}

npm_install "@anthropic-ai/claude-code"  claude
npm_install ccusage                       ccusage
npm_install "@mixedbread/mgrep"           mgrep
npm_install agent-browser                 agent-browser

# --- bun global tools ---

bun_install() {
    local pkg="$1" cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif need bun; then
        bun install -g "$pkg" && ok "Installed $cmd (bun)"
    fi
}

bun_install "github:tobi/qmd" qmd

# --- uv tools ---

uv_install() {
    local pkg="$1" cmd="${2:-$1}"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif need uv; then
        uv tool install "$pkg" && ok "Installed $cmd (uv)"
    fi
}

uv_install_from_source() {
    local dir="$1" cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif [ -d "$dir" ] && need uv; then
        uv tool install "$dir" && ok "Installed $cmd (uv, from source)"
    else
        warn "Source dir $dir not found — skipping $cmd"
    fi
}

uv_install claude-monitor claude-monitor
uv_install_from_source "$HOME/code/oghma" oghma
uv_install_from_source "$HOME/code/lustro" lustro

# --- rustup setup ---
# On NixOS, rustup is a system package (curl installer won't work — dynamic linking).
# On macOS, install via curl if missing.

if command -v rustup &>/dev/null; then
    if ! rustup toolchain list 2>/dev/null | grep -q stable; then
        rustup toolchain install stable && ok "Installed Rust stable via rustup"
    else
        skip "rustup + stable toolchain already installed"
    fi
    export PATH="$HOME/.cargo/bin:$PATH"
elif [ "$OS" = "Darwin" ] && need curl; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path && ok "Installed rustup"
    export PATH="$HOME/.cargo/bin:$PATH"
else
    warn "rustup not found — install via system package manager"
fi

# --- cargo tools (from local source) ---

cargo_install() {
    local dir="$1" cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif [ -d "$dir" ] && command -v cargo &>/dev/null; then
        # NixOS: help pkg-config find openssl.dev
        if [ -d /run/current-system/sw/lib/pkgconfig ]; then
            export PKG_CONFIG_PATH="/run/current-system/sw/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
        fi
        cargo install --path "$dir" && ok "Installed $cmd (cargo)" || warn "Failed to build $cmd"
    else
        warn "Source dir $dir not found or cargo missing — skipping $cmd"
    fi
}

cargo_install "$HOME/code/pplx"      compound-pplx
cargo_install "$HOME/code/resurface" resurface

# --- go tools ---

go_install() {
    local pkg="$1" cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        skip "$cmd already installed"
    elif need go; then
        go install "$pkg" && ok "Installed $cmd (go)"
    fi
}

go_install "github.com/steipete/gogcli/cmd/gog@latest" gog

# --- OpenCode (Linux only — binary download) ---

if [ "$OS" = "Linux" ]; then
    if command -v opencode &>/dev/null; then
        skip "opencode already installed"
    elif need curl; then
        OPENCODE_URL="https://github.com/sst/opencode/releases/latest/download/opencode-linux-x64.tar.gz"
        curl -sL "$OPENCODE_URL" -o /tmp/opencode.tar.gz && tar xzf /tmp/opencode.tar.gz -C "$HOME/.local/bin" opencode && chmod +x "$HOME/.local/bin/opencode" && rm /tmp/opencode.tar.gz && ok "Installed opencode (binary)"
    fi
else
    skip "opencode — Linux only, skipping"
fi

# --- Gemini CLI ---

npm_install "@google/gemini-cli" gemini

# bird is macOS-only (brew tap: steipete/tap/bird) — skip on Linux
if [ "$OS" = "Darwin" ]; then
    if command -v bird &>/dev/null; then
        skip "bird already installed"
    elif command -v brew &>/dev/null; then
        brew install steipete/tap/bird && ok "Installed bird (brew)"
    else
        warn "bird requires brew — skipping"
    fi
else
    skip "bird — macOS only, skipping"
fi

# ── 4. .zshenv.local template ─────────────────────────────────────────────

echo ""
echo "=== Config ==="

if [ ! -f "$HOME/.zshenv.local" ]; then
    cat > "$HOME/.zshenv.local" << 'EOF'
# Machine-local environment — fill in secrets
# Sourced by .zshenv if present

# export ANTHROPIC_API_KEY=""
# export CLAUDE_CODE_OAUTH_TOKEN=""
# export OPENROUTER_API_KEY=""
# export OPENAI_API_KEY=""
# export GOOGLE_API_KEY=""
# export XAI_API_KEY=""
# export PERPLEXITY_API_KEY=""
# export TELEGRAM_BOT_TOKEN=""
# export TELEGRAM_CHAT_ID=""
EOF
    ok "Created ~/.zshenv.local template — fill in secrets"
else
    skip ".zshenv.local already exists"
fi

# ── 5. NixOS hint ─────────────────────────────────────────────────────────

if $NIXOS; then
    echo ""
    echo "=== NixOS ==="
    echo "Run this to apply system packages:"
    echo "  cd ~/code/pharos && git pull && sudo nixos-rebuild switch --flake .#pharos"
fi

# ── Done ───────────────────────────────────────────────────────────────────

echo ""
echo "=== Done ==="
echo "Next steps:"
echo "  1. Fill in secrets in ~/.zshenv.local"
echo "  2. exec zsh (reload shell)"
echo "  3. gh auth login (if not already authenticated)"
if $NIXOS; then
    echo "  4. sudo nixos-rebuild switch --flake ~/code/pharos#pharos"
fi
