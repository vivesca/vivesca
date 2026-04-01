# gemmule — dormant capsule containing everything needed to regenerate the soma.
#
# Contains: OS, runtimes, tools, op CLI. No secrets, no state.
# Push to registry (multi-arch):
#   docker buildx build --platform linux/amd64,linux/arm64 \
#     -t ghcr.io/terryli-vt/gemmule:latest --push .
#
# Regenerate soma:  fly machine run ghcr.io/terryli-vt/gemmule:latest ...
#                   then run: soma-activate (injects secrets, clones repos, links)

FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Hong_Kong
ENV LANG=C.UTF-8

# System packages
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    curl wget git tmux htop jq unzip \
    zsh python3 python3-pip python3-venv python3-dev \
    sqlite3 libsqlite3-dev \
    ca-certificates gnupg openssh-server sudo \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Runtimes (as system-level installs)
# ---------------------------------------------------------------------------

# Go
ARG GO_VERSION=1.24.1
ARG TARGETARCH
RUN wget -q "https://go.dev/dl/go${GO_VERSION}.linux-${TARGETARCH}.tar.gz" -O /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

# Node.js 22
ARG NODE_MAJOR=22
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL "https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key" \
       | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
       > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update -qq && apt-get install -y -qq nodejs \
    && rm -rf /var/lib/apt/lists/*

# Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# 1Password CLI
ARG OP_VERSION=2.30.3
ARG TARGETARCH
RUN curl -sS "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_${TARGETARCH}_v${OP_VERSION}.zip" \
    -o /tmp/op.zip \
    && unzip -o /tmp/op.zip op -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/op \
    && rm /tmp/op.zip

# ---------------------------------------------------------------------------
# User: terry
# ---------------------------------------------------------------------------

RUN adduser --disabled-password --gecos "" terry \
    && usermod -aG sudo terry \
    && echo "terry ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/terry \
    && chsh -s "$(which zsh)" terry

USER terry
WORKDIR /home/terry
ENV HOME=/home/terry
ENV PATH="${HOME}/.local/bin:${HOME}/bin:${HOME}/go/bin:${HOME}/.bun/bin:/usr/local/go/bin:${HOME}/germline/effectors:${PATH}"

# uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Bun
RUN curl -fsSL https://bun.sh/install | bash

# ---------------------------------------------------------------------------
# System CLI tools (pre-built binaries — no cargo compile)
# ---------------------------------------------------------------------------

# starship prompt (install to ~/.local/bin)
RUN mkdir -p ~/.local/bin && curl -sS https://starship.rs/install.sh | sh -s -- -y -b ~/.local/bin

# Arch mapping for Rust binaries: amd64->x86_64, arm64->aarch64
ARG TARGETARCH
RUN RUST_ARCH=$([ "$TARGETARCH" = "arm64" ] && echo "aarch64" || echo "x86_64") \
    && echo "Building for ${RUST_ARCH}" \
    # eza (modern ls)
    && curl -sL "https://github.com/eza-community/eza/releases/latest/download/eza_${RUST_ARCH}-unknown-linux-gnu.tar.gz" \
       | tar xz -C ~/.local/bin/ \
    # bat (modern cat)
    && curl -sL "https://github.com/sharkdp/bat/releases/download/v0.25.0/bat-v0.25.0-${RUST_ARCH}-unknown-linux-gnu.tar.gz" \
       | tar xz --strip-components=1 -C /tmp && mv /tmp/bat ~/.local/bin/bat \
    # fd (modern find)
    && curl -sL "https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-${RUST_ARCH}-unknown-linux-gnu.tar.gz" \
       | tar xz --strip-components=1 -C /tmp && mv /tmp/fd ~/.local/bin/fd

# zoxide (smart cd) — install script auto-detects arch
RUN curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh -s -- --bin-dir ~/.local/bin

# ---------------------------------------------------------------------------
# Custom CLIs — all Python, installed by soma-activate from ~/bin/
# No Rust compilation needed. Golems build these as single-file Python scripts.
# Tools: noesis, consilium, fasti, keryx, moneo, sarcio, grapho, caelum,
#        stips, anam, auceps, pondus, exauro
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# pipx tools
# ---------------------------------------------------------------------------

RUN ~/.local/bin/uv tool install llm \
    && ~/.local/bin/uv tool install openai \
    && ~/.local/bin/uv tool install sqlite-utils \
    && ~/.local/bin/uv tool install tqdm \
    && ~/.local/bin/uv tool install httpx \
    && ~/.local/bin/uv tool install tabulate \
    && ~/.local/bin/uv tool install python-ulid \
    && ~/.local/bin/uv tool install puremagic \
    || true

# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------

RUN npm install -g @anthropic-ai/claude-code 2>/dev/null || true

# ---------------------------------------------------------------------------
# Directory scaffold
# ---------------------------------------------------------------------------

RUN mkdir -p ~/bin ~/code ~/scripts ~/notes \
    ~/epigenome/chromatin ~/epigenome/marks \
    ~/.claude/hooks ~/.claude/skills \
    ~/.ssh && chmod 700 ~/.ssh

# ---------------------------------------------------------------------------
# Shell config (static — secrets injected at activation)
# ---------------------------------------------------------------------------

# Shell and tmux config
COPY --chown=terry:terry docker/zshrc /home/terry/.zshrc
COPY --chown=terry:terry docker/tmux.conf /home/terry/.tmux.conf

# Git config
RUN git config --global user.name "Terry Li" \
    && git config --global user.email "terry.li.hm@gmail.com" \
    && git config --global init.defaultBranch main \
    && git config --global pull.rebase false \
    && git config --global push.autoSetupRemote true

# SSH hardening (for when running as a full VM)
USER root
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config 2>/dev/null || true \
    && sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config 2>/dev/null || true

USER terry

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

LABEL org.opencontainers.image.title="gemmule"
LABEL org.opencontainers.image.description="Dormant capsule for vivesca soma regeneration"
LABEL org.opencontainers.image.source="https://github.com/terryli-vt/vivesca"

CMD ["zsh"]
