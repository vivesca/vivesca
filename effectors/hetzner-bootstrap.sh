#!/usr/bin/env bash
# Hetzner VPS Bootstrap for Claude Code
# Run as root on a fresh Ubuntu 22.04 VPS
# Usage: ssh root@<IP> 'bash -s' < hetzner-bootstrap.sh

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: hetzner-bootstrap.sh"
    echo ""
    echo "Bootstrap a fresh Hetzner Ubuntu 22.04 VPS for Claude Code."
    echo "Creates user 'vivesca', installs Node.js, Claude Code, Tailscale, pnpm, uv."
    echo "Must be run as root: ssh root@<IP> 'bash -s' < hetzner-bootstrap.sh"
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root." >&2
   exit 1
fi

echo "=== Hetzner Claude Code Bootstrap ==="

# 1. System updates
apt-get update && apt-get upgrade -y
apt-get install -y curl git tmux htop jq unzip build-essential

# 2. Create user 'vivesca' with sudo
if ! id vivesca &>/dev/null; then
  adduser --disabled-password --gecos "" vivesca
  usermod -aG sudo vivesca
  echo "vivesca ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vivesca

  # Copy SSH keys from root
  mkdir -p ~vivesca/.ssh
  cp /root/.ssh/authorized_keys ~vivesca/.ssh/
  chown -R vivesca:vivesca ~vivesca/.ssh
  chmod 700 ~vivesca/.ssh
  chmod 600 ~vivesca/.ssh/authorized_keys
fi

# 3. Install Node.js (LTS via fnm)
sudo -u vivesca bash -c '
  curl -fsSL https://fnm.vercel.app/install | bash
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env)"
  fnm install --lts
  fnm default lts-latest
'

# 4. Install Claude Code
sudo -u vivesca bash -c '
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env)"
  npm install -g @anthropic-ai/claude-code
'

# 5. Install Tailscale (zero-config VPN for SSH without port forwarding)
curl -fsSL https://tailscale.com/install.sh | sh
echo ""
echo ">>> Run 'sudo tailscale up' after bootstrap to authenticate Tailscale"

# 6. Install pnpm
sudo -u vivesca bash -c '
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env)"
  npm install -g pnpm
'

# 7. Install uv (Python)
sudo -u vivesca bash -c '
  curl -LsSf https://astral.sh/uv/install.sh | sh
'

# 8. tmux config (basic - will be replaced by dotfiles later)
sudo -u vivesca bash -c 'cat > ~/.tmux.conf << "TMUX"
set -g prefix C-a
unbind C-b
bind C-a send-prefix
set -g mouse on
set -g history-limit 50000
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
set -g base-index 1
set -g escape-time 0
set -g status-style "bg=#1e1e2e,fg=#cdd6f4"
TMUX'

# 9. Clone repos (will need auth - just create dirs for now)
sudo -u vivesca bash -c '
  mkdir -p ~/code ~/scripts ~/code/epigenome/chromatin ~/skills
  echo ">>> Clone your repos:"
  echo "  git clone <agent-config-repo> ~/agent-config"
  echo "  git clone <skills-repo> ~/skills"
  echo "  git clone <vault-repo> ~/code/epigenome/chromatin"
'

# 10. Harden SSH
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "  1. SSH in as vivesca: ssh vivesca@<IP>"
echo "  2. Authenticate Tailscale: sudo tailscale up"
echo "  3. Authenticate Claude Code: claude (follow browser OAuth)"
echo "  4. Clone your repos (agent-config, skills, vault)"
echo "  5. Set up git credentials: gh auth login"
echo ""
echo "After Tailscale, connect via: ssh vivesca@<tailscale-hostname>"
echo "Then the public IP doesn't matter anymore."
