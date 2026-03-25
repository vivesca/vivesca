# NixOS on AWS EC2 — Research Notes (Feb 2026)

## Reliable Sources
- wiki.nixos.org/wiki/Install_NixOS_on_Amazon_EC2 — sparse; directs to nixos-generators
- raw.githubusercontent.com/NixOS/nixpkgs/master/nixos/modules/virtualisation/amazon-image.nix — source of truth for module options
- github.com/nix-community/nixos-anywhere-examples — official example flake (Hetzner/DO/generic)
- nix-community.github.io/nixos-anywhere/quickstart.html — best quickstart
- nix.dev/tutorials/nixos/provisioning-remote-machines.html — good disko+nixos-anywhere tutorial
- gist.github.com/kaznak/734c6a3c56703c8690bab43d59e36016 — working EC2 configuration.nix example
- nixos.github.io/amis/ — official AMI list (JS-rendered; use AWS CLI or Terraform snippets)
- github.com/nix-community/disko/issues/441 — amazon-image.nix + disko conflict and fix

## Key Technical Facts

### amazon-image.nix module
- Import path: `"${modulesPath}/virtualisation/amazon-image.nix"`
- Sets `ec2.hvm = true` for HVM instances
- Boot: GRUB with serial console (ttyS0), supports EFI or legacy BIOS via `cfg.efi`
- Kernel modules: ENA (elastic network), xen-blkfront, NVMe
- Filesystems: uses `lib.mkDefault` for ext4 root + vfat ESP — so disko CAN override without lib.mkForce
- NTP: 169.254.169.123 (EC2 hypervisor)
- Hostname: from EC2 metadata service
- SSM Agent: enabled by default
- Blacklisted: nouveau, xen_fbfront

### disko + amazon-image.nix conflict
- Issue #441: fileSystems conflict when using non-ext4 (e.g. btrfs)
- Fix: amazon-image.nix now uses lib.mkDefault for filesystems, so disko CAN override
- If still conflicts: use `lib.mkForce` in disko config or in a module overlay

### EC2 Disk Device Names
- Nitro instances (t3, c5, m5, c6, etc.): root disk appears as /dev/nvme0n1
- Console shows /dev/xvda but inside Linux it's /dev/nvme0n1
- Device order NOT guaranteed stable — use /dev/disk/by-id/ or /dev/disk/by-label/ in production
- For disko: use `device = "/dev/nvme0n1"` for Nitro t3; `device = "/dev/xvda"` for older t2

### nixos-anywhere kexec requirements
- Target must run x86_64 Linux with kexec support
- Minimum 1 GB RAM (official). Practical: t3.micro (1 GB) is borderline — recommend t3.small (2 GB) for the conversion, then resize down
- Root SSH access OR passwordless sudo non-root user
- No NixOS installer needed — kexec bootstraps it

### nixos-anywhere EC2 conversion flow
1. Launch Ubuntu/Amazon Linux EC2 (t3.small+ recommended)
2. Enable root SSH: `sudo passwd root` + `PermitRootLogin yes` in sshd_config, OR use `--sudo` flag if non-root with passwordless sudo
3. From local machine: `nix run github:nix-community/nixos-anywhere -- --flake .#myhost root@<IP>`
4. nixos-anywhere kexecs into NixOS installer, runs disko, installs, reboots
5. Update known_hosts after reboot

### Boot loader: EC2 is BIOS, not EFI (for older instances)
- Nitro instances support EFI but most practical EC2 deployments use BIOS/legacy GRUB
- Disko config: use EF02 (BIOS boot) 1MB partition + EF00 ESP 500MB for dual compat
- OR: pure BIOS with just EF02 partition (no /boot ESP)
- In flake: `boot.loader.grub.efiSupport = true; boot.loader.grub.efiInstallAsRemovable = true;` if using EFI

## Node.js Package Names in nixpkgs
- nodejs_22, nodejs_24, nodejs_25 all exist in nixpkgs master
- nodejs_22 is current LTS (2026); nodejs_24 exists but was not LTS at research time
- For "latest LTS": use `pkgs.nodejs_22` or `pkgs.nodejs` (tracks current LTS)
- fnm: available as `pkgs.fnm`; on NixOS server installs, direct nodejs_XX is simpler

## fail2ban + OpenSSH 9.8 Bug
- OpenSSH 9.8 renamed daemon sessions to "sshd-session" — fail2ban regex misses it
- Fix: override package with two upstream patches (see issue #48972 on NixOS Discourse)
- Status as of Feb 2026: fix in upstream fail2ban but may not be in NixOS 24.11 package
- Always include the package override in EC2 configs to be safe

## Tailscale NixOS Module
- `services.tailscale.enable = true`
- `networking.firewall.trustedInterfaces = ["tailscale0"]`
- `networking.firewall.allowedUDPPorts = [config.services.tailscale.port]`
- `networking.firewall.checkReversePath = "loose"` (needed for exit nodes, safe to set generally)
- authKeyFile path for unattended auth

## Misinformation Patterns
- "Use amazon-image.nix for nixos-anywhere" — this CONFLICTS with disko. Skip it for nixos-anywhere deploys; the module is for building AMIs, not for nixos-anywhere installs
- "t2.micro works for nixos-anywhere kexec" — borderline at 1 GB; use t3.small
- Device name "/dev/xvda" — only valid for t2; Nitro instances use /dev/nvme0n1
- "lib.mkForce required for disko + amazon-image" — only if using non-ext4; with ext4 disko it should work since amazon-image uses lib.mkDefault
