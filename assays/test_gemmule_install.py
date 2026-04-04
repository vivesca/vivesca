from __future__ import annotations

import os
import subprocess
from pathlib import Path

INSTALL_SCRIPT = Path.home() / "germline" / "gemmule" / "install.sh"
DOCKERFILE = Path.home() / "germline" / "Dockerfile"
GEMMULE_DIR = Path.home() / "germline" / "gemmule"
LEGACY_DOCKER_DIR = Path.home() / "germline" / "docker"


def test_install_script_exists() -> None:
    assert INSTALL_SCRIPT.exists()


def test_install_script_is_executable() -> None:
    assert os.access(INSTALL_SCRIPT, os.X_OK)


def test_install_script_has_bash_shebang() -> None:
    first_line = INSTALL_SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


def test_install_script_passes_bash_syntax_check() -> None:
    result = subprocess.run(
        ["bash", "-n", str(INSTALL_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_install_script_has_required_sections() -> None:
    source = INSTALL_SCRIPT.read_text()
    required_sections = [
        "# 1. System packages",
        "# 2. Go",
        "# 3. Node.js 22",
        "# 4. Tailscale",
        "# 5. gh CLI",
        "# 6. 1Password CLI",
        "# 7. Create terry user",
        "# 8. uv, Bun",
        "# 9. starship, eza, bat, fd, zoxide",
        "# 10. npm globals",
        "# 11. uv tools",
        "# 12. rustup",
        "# 13. Playwright",
        "# 14. Directory scaffold",
        "# 15. Git config",
        "# 16. SSH hardening",
    ]
    for section in required_sections:
        assert section in source


def test_install_script_has_arch_mapping() -> None:
    source = INSTALL_SCRIPT.read_text()
    assert "MACHINE_ARCH=$(uname -m)" in source
    assert "x86_64)  GO_ARCH=amd64; RUST_ARCH=x86_64; OP_ARCH=amd64 ;;" in source
    assert "aarch64) GO_ARCH=arm64; RUST_ARCH=aarch64; OP_ARCH=arm64 ;;" in source


def test_install_script_installs_required_tools() -> None:
    source = INSTALL_SCRIPT.read_text()
    expected_entries = [
        "@anthropic-ai/claude-code",
        "@google/gemini-cli",
        "@openai/codex",
        "agent-browser",
        "ccusage",
        "pnpm",
        "playwright",
        "rustup",
        "gh",
        "ripgrep",
        "build-essential",
    ]
    for entry in expected_entries:
        assert entry in source


def test_dockerfile_uses_install_wrapper() -> None:
    source = DOCKERFILE.read_text()
    assert "COPY gemmule/install.sh /tmp/install.sh" in source
    assert "RUN chmod +x /tmp/install.sh && /tmp/install.sh" in source
    assert "COPY --chown=terry:terry gemmule/zshrc /home/terry/.zshrc" in source
    assert "COPY --chown=terry:terry gemmule/tmux.conf /home/terry/.tmux.conf" in source
    assert "docker/zshrc" not in source
    assert "docker/tmux.conf" not in source


def test_shell_assets_live_in_gemmule_directory() -> None:
    assert (GEMMULE_DIR / "zshrc").exists()
    assert (GEMMULE_DIR / "tmux.conf").exists()


def test_legacy_docker_assets_removed() -> None:
    assert not (LEGACY_DOCKER_DIR / "zshrc").exists()
    assert not (LEGACY_DOCKER_DIR / "tmux.conf").exists()
