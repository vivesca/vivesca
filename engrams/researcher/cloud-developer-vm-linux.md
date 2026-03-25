# Cloud Developer VM Linux Setup Research (Feb 2026)

## Context
Research for EC2 t3.micro/small running Claude Code + systemd timers + frequent ad-hoc tool installs.
Existing setup: NixOS. Alternatives considered: Ubuntu + Nix overlay.

## Verdict Summary
Ubuntu 24.04 LTS + shell bootstrap script (cloud-init or Ansible-pull) is the dominant practical pattern.
NixOS on EC2 is a friction trap for the "ad-hoc tool install" pattern. Nix-on-Ubuntu is the best of both worlds if you want declarative dev shells.

## Key Sources That Worked Well
- discourse.nixos.org — best source for NixOS practical pain, especially npm/binary threads
- fd93.me/nixos-to-ubuntu — personal migration writeup; WebFetch works; honest about venv/pip/npm failures
- rasmuskirk.com/articles/2024-07-24_dont-use-nixos/ — best "Nix without NixOS" argument; WebFetch works
- pierrezemb.fr/posts/nixos-good-bad-ugly/ — cloud engineer experience with NixOS binary issues; WebFetch works
- github.com/Dicklesworthstone/agentic_coding_flywheel_setup — Ubuntu 25.10 AI agent bootstrap; real-world reference
- homelabstarter.com/homelab-immutable-os-comparison/ — immutable distros (CoreOS/Flatcar/Talos) practical limits; WebFetch works
- linuxways.net/best-of-linux/amazon-linux-vs-ubuntu-for-ec2/ — AL2023 vs Ubuntu developer comparison; WebFetch works
- news.ycombinator.com/item?id=46690907 — HN "Claude Code safely" thread; ubuntu+bubblewrap consensus

## NixOS Binary Compatibility — Confirmed Pain Points
- `npm install -g`: fails by default (nix store read-only). Workaround: set npm prefix to user home.
- Prebuilt npm binaries (Electron, etc.): dynamically linked to missing paths. nix-ld fixes ~90% but not all.
- `cargo install`: frequently hits missing system lib paths (openssl, etc.) not in nix build env.
- Python venv: doesn't work correctly. pip is crippled. NixOS-packaged Python doesn't pick up NIX_LD env.
- Go binaries: generally OK if compiled from source; prebuilt GitHub releases fail.
- Solutions exist (patchelf, buildFHSEnv, steam-run) but all require per-binary maintenance.
- **nix-ld is not a silver bullet**: it addresses the linker stub but not missing shared libraries.

## Amazon Linux 2023 Assessment
- PRO: Better EC2 integration, preloaded AWS CLI, AWS-tuned kernel. ~15% faster pod startups vs Ubuntu in some tests.
- CON: Much smaller community, fewer third-party tutorials, less dev tool coverage.
- VERDICT: Only worth it if your workload is AWS infra tooling. For general dev/agent work, Ubuntu wins.

## Immutable Distros Assessment
- Fedora CoreOS, Flatcar, Talos, Bottlerocket: ALL designed for containers-only workflows.
- Read-only root filesystem means `npm install -g`, `cargo install`, `go install` don't work without containers.
- Talos/Bottlerocket: no SSH shell at all.
- VERDICT: Wrong tool for "developer machine that installs ad-hoc tools."

## Reproducibility Approaches Ranked
1. **cloud-init user data** (simplest): Shell script in EC2 launch template. Runs once on first boot. Not idempotent by default (some modules are). Good for "bootstrap to known state."
2. **Ansible-pull** (best for drift prevention): `ansible-pull` from a git repo. Runs on boot via cloud-init. Fully idempotent if written correctly. Good for team shared VMs.
3. **chezmoi + Ansible**: chezmoi for dotfiles, Ansible for system packages. Popular pattern in 2024. Good for personal machines.
4. **Nix home-manager on Ubuntu**: Declarative user env without NixOS system friction. home-manager.systemd supports user timers. Best for Nix-familiar devs who want reproducibility without OS constraints.
5. **Full NixOS** (most powerful, most friction): Full system declarative. nixos-rebuild switch. Best for stable, well-understood services. Fights every "install something new" workflow.

## Real-World AI Agent VM Pattern
- github.com/Dicklesworthstone/agentic_coding_flywheel_setup uses Ubuntu 25.10 with a YAML manifest + shell installer.
- claude-code-vm project uses Debian.
- HN Claude Code thread: Ubuntu 22.04/24.04 with bubblewrap is the consensus for isolation.
- No one is using NixOS for agent sandboxing in the public examples found.

## Misinformation Patterns
- "NixOS is reproducible" — true for hermetic Nix builds; does NOT mean you can run arbitrary binaries reliably.
- "nix-ld solves binary compat" — it solves the linker stub; shared library paths still need manual configuration per binary.
- "Amazon Linux is faster" — the performance difference on a t3 instance is negligible for dev workloads.
- "Fedora CoreOS is good for general cloud VMs" — only if everything is containerized.
