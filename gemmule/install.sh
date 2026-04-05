#!/usr/bin/env bash
# gemmule/install.sh — shared base-image installer for soma and ganglion.
#
# Run as root:
#   sudo bash gemmule/install.sh
#
# Idempotent, arch-aware, no secrets.

set -euo pipefail

USER_NAME="terry"
USER_HOME="/home/${USER_NAME}"
GO_VERSION="1.24.1"
NODE_MAJOR=22
OP_VERSION="2.30.3"
PLAYWRIGHT_VERSION="1.52.0"

MACHINE_ARCH=$(uname -m)
case "$MACHINE_ARCH" in
  x86_64)  GO_ARCH=amd64; RUST_ARCH=x86_64; OP_ARCH=amd64 ;;
  aarch64) GO_ARCH=arm64; RUST_ARCH=aarch64; OP_ARCH=arm64 ;;
  *) echo "Unsupported arch: $MACHINE_ARCH"; exit 1 ;;
esac

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[32m[ok]\033[0m %s\n' "$*"; }
skip() { printf '    \033[33m[skip]\033[0m %s\n' "$*"; }

run_as_terry() {
  sudo -u "$USER_NAME" HOME="$USER_HOME" bash -lc "$1"
}

have_package() {
  dpkg -s "$1" >/dev/null 2>&1
}

ensure_apt_package() {
  local package_name="$1"
  if have_package "$package_name"; then
    skip "$package_name"
  else
    apt-get install -y -qq --no-install-recommends "$package_name"
    ok "$package_name"
  fi
}

ensure_line() {
  local line="$1"
  local file_path="$2"
  touch "$file_path"
  if grep -Fqx "$line" "$file_path"; then
    skip "$file_path: $line"
  else
    printf '%s\n' "$line" >> "$file_path"
    ok "$file_path updated"
  fi
}

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

# 1. System packages
log "System packages"
apt-get update -qq
SYSTEM_PACKAGES=(
  build-essential
  ca-certificates
  curl
  file
  fzf
  git
  git-lfs
  gnupg
  htop
  jq
  libsqlite3-dev
  libssl-dev
  lsof
  mosh
  openssh-server
  pkg-config
  python3
  python3-dev
  python3-pip
  python3-venv
  ripgrep
  sqlite3
  sudo
  tmux
  unzip
  wget
  zsh
)
for package_name in "${SYSTEM_PACKAGES[@]}"; do
  ensure_apt_package "$package_name"
done
rm -rf /var/lib/apt/lists/*

# 2. Go
log "Go ${GO_VERSION}"
if command -v go >/dev/null 2>&1 && go version | grep -q "go${GO_VERSION} "; then
  skip "go ${GO_VERSION}"
else
  wget -q "https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz" -O /tmp/go.tar.gz
  rm -rf /usr/local/go
  tar -C /usr/local -xzf /tmp/go.tar.gz
  rm -f /tmp/go.tar.gz
  ok "go ${GO_VERSION}"
fi

# 3. Node.js 22
log "Node.js ${NODE_MAJOR}"
if command -v node >/dev/null 2>&1 && node --version | grep -q "^v${NODE_MAJOR}\."; then
  skip "node ${NODE_MAJOR}"
else
  mkdir -p /etc/apt/keyrings
  rm -f /etc/apt/keyrings/nodesource.gpg /etc/apt/sources.list.d/nodesource.list
  curl -fsSL "https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key" \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
  printf 'deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_%s.x nodistro main\n' "$NODE_MAJOR" \
    > /etc/apt/sources.list.d/nodesource.list
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends nodejs
  rm -rf /var/lib/apt/lists/*
  ok "node $(node --version)"
fi

# 4. Tailscale
log "Tailscale"
if command -v tailscale >/dev/null 2>&1; then
  skip "tailscale"
else
  curl -fsSL https://tailscale.com/install.sh | sh
  ok "tailscale"
fi

# 5. gh CLI
log "GitHub CLI"
if command -v gh >/dev/null 2>&1; then
  skip "gh"
else
  (type -p wget >/dev/null || apt-get install -y -qq wget) \
    && mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -qO "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat "$out" | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
         | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update -qq && apt-get install -y -qq gh \
    && rm -f "$out" && rm -rf /var/lib/apt/lists/*
  ok "gh"
fi

# 6. 1Password CLI
log "1Password CLI ${OP_VERSION}"
if command -v op >/dev/null 2>&1 && op --version 2>/dev/null | grep -q "$OP_VERSION"; then
  skip "op ${OP_VERSION}"
else
  curl -fsSL "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_${OP_ARCH}_v${OP_VERSION}.zip" -o /tmp/op.zip
  rm -f /usr/local/bin/op
  unzip -o /tmp/op.zip op -d /usr/local/bin/
  chmod +x /usr/local/bin/op
  rm -f /tmp/op.zip
  ok "op ${OP_VERSION}"
fi

# 7. Create terry user
log "User ${USER_NAME}"
if id "$USER_NAME" >/dev/null 2>&1; then
  skip "${USER_NAME} user"
else
  adduser --disabled-password --gecos "" "$USER_NAME"
  ok "${USER_NAME} user"
fi
usermod -aG sudo "$USER_NAME"
printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$USER_NAME" > "/etc/sudoers.d/${USER_NAME}"
chmod 0440 "/etc/sudoers.d/${USER_NAME}"
chsh -s "$(command -v zsh)" "$USER_NAME"

# 8. uv, Bun
log "uv and Bun"
if run_as_terry 'command -v uv >/dev/null 2>&1'; then
  skip "uv"
else
  run_as_terry 'curl -LsSf https://astral.sh/uv/install.sh | sh'
  ok "uv"
fi
if run_as_terry 'command -v bun >/dev/null 2>&1'; then
  skip "bun"
else
  run_as_terry 'curl -fsSL https://bun.sh/install | bash'
  ok "bun"
fi

# 9. starship, eza, bat, fd, zoxide
log "User-space binaries"
run_as_terry 'mkdir -p ~/.local/bin'
if run_as_terry 'command -v starship >/dev/null 2>&1'; then
  skip "starship"
else
  run_as_terry 'curl -fsSL https://starship.rs/install.sh | sh -s -- -y -b ~/.local/bin'
  ok "starship"
fi
if run_as_terry 'command -v eza >/dev/null 2>&1'; then
  skip "eza"
else
  run_as_terry "curl -fsSL https://github.com/eza-community/eza/releases/latest/download/eza_${RUST_ARCH}-unknown-linux-gnu.tar.gz | tar -xz -C ~/.local/bin"
  ok "eza"
fi
if run_as_terry 'command -v bat >/dev/null 2>&1'; then
  skip "bat"
else
  run_as_terry "tmp_dir=\$(mktemp -d) && curl -fsSL https://github.com/sharkdp/bat/releases/download/v0.25.0/bat-v0.25.0-${RUST_ARCH}-unknown-linux-gnu.tar.gz | tar -xz --strip-components=1 -C \"\$tmp_dir\" && install -m 0755 \"\$tmp_dir/bat\" ~/.local/bin/bat && rm -rf \"\$tmp_dir\""
  ok "bat"
fi
if run_as_terry 'command -v fd >/dev/null 2>&1'; then
  skip "fd"
else
  run_as_terry "tmp_dir=\$(mktemp -d) && curl -fsSL https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-${RUST_ARCH}-unknown-linux-gnu.tar.gz | tar -xz --strip-components=1 -C \"\$tmp_dir\" && install -m 0755 \"\$tmp_dir/fd\" ~/.local/bin/fd && rm -rf \"\$tmp_dir\""
  ok "fd"
fi
if run_as_terry 'command -v zoxide >/dev/null 2>&1'; then
  skip "zoxide"
else
  run_as_terry 'curl -fsSL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh -s -- --bin-dir ~/.local/bin'
  ok "zoxide"
fi

# 10. npm globals
log "npm globals"
NPM_PACKAGES=(
  @anthropic-ai/claude-code
  @google/gemini-cli
  @openai/codex
  agent-browser
  agnix
  ccusage
  pnpm
)
for package_name in "${NPM_PACKAGES[@]}"; do
  if npm list -g --depth=0 "$package_name" >/dev/null 2>&1; then
    skip "$package_name"
  else
    npm install -g "$package_name"
    ok "$package_name"
  fi
done

# 11. uv tools
log "uv tools"
UV_TOOL_PACKAGES=(
  llm
  openai
  sqlite-utils
  tqdm
  httpx
  tabulate
  python-ulid
  puremagic
)
for package_name in "${UV_TOOL_PACKAGES[@]}"; do
  if run_as_terry "~/.local/bin/uv tool list | grep -q '^${package_name} '"; then
    skip "$package_name"
  else
    run_as_terry "~/.local/bin/uv tool install ${package_name}"
    ok "$package_name"
  fi
done

# 12. rustup
log "rustup"
if run_as_terry 'source ~/.cargo/env 2>/dev/null && command -v rustc >/dev/null 2>&1'; then
  skip "rustup"
else
  run_as_terry "curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable --target ${RUST_ARCH}-unknown-linux-gnu"
  ok "rustup"
fi

# 13. Playwright
log "Playwright"
if run_as_terry "[ -x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome ]" 2>/dev/null; then
  skip "playwright chromium"
else
  PLAYWRIGHT_BROWSERS_PATH="$USER_HOME/.cache/ms-playwright" HOME="$USER_HOME" sudo -u "$USER_NAME" npx -y "playwright@${PLAYWRIGHT_VERSION}" install --with-deps chromium
  ok "playwright chromium"
fi

# 14. Directory scaffold
log "Directory scaffold"
run_as_terry 'mkdir -p ~/bin ~/code ~/scripts ~/epigenome/chromatin ~/epigenome/marks ~/.claude/hooks ~/.claude/skills ~/.claude/agents ~/.ssh ~/germline'
chmod 700 "${USER_HOME}/.ssh"
ok "directories"

# 15. Git config
log "Git config"
run_as_terry 'git config --global user.name "Terry Li"'
run_as_terry 'git config --global user.email "terry.li.hm@gmail.com"'
run_as_terry 'git config --global init.defaultBranch main'
run_as_terry 'git config --global pull.rebase false'
run_as_terry 'git config --global push.autoSetupRemote true'
ok "git config"

# 16. SSH hardening
log "SSH hardening"
ensure_line "PasswordAuthentication no" /etc/ssh/sshd_config
ok "sshd_config"
