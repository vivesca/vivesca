# Mac Security Audit — March 2026

iMac, home office. Physical access risk low (family home).

## Critical

### Firewall disabled
- No inbound filtering. SSH open (Blink/mosh). Home network shared with family devices.
- **Fix:** Enable firewall, allow SSH/mosh through.

### FileVault off
- Unencrypted disk. Lower priority for a desktop that doesn't leave the house, but still protects against theft or repair scenarios.
- **Fix:** Enable FileVault. Encrypts in background.

## Moderate

### Public Folder shared with guest access (SMB, read-write)
- Anyone on LAN can write to `/Users/terry/Public` without auth.
- **Fix:** Disable sharing or at minimum disable guest access.

### Grammarly — Accessibility + 3 LaunchAgents
- Accessibility = can read keystrokes. Three persistent LaunchAgents (Shepherd, Uninstaller, UpdateService).
- **Fix:** Remove if unused.

### Stale TCC grants
- Old versioned binaries still have permissions: Node 25.2.1, Claude Code 2.1.49/2.1.50, OpenCode 1.2.1/1.2.5.
- **Fix:** Prune dead paths from Privacy & Security settings.

### OnVue (Pearson exam proctoring)
- Camera + Microphone + Input Monitoring. Standard for proctored exams.
- **Fix:** Remove after GARP exam (2026-04-04).

## Informational

- SIP enabled, Gatekeeper enabled — good.
- Mullvad VPN daemon present — good.
- ~55 LaunchAgents, mostly `com.terry.*` — periodic prune worthwhile.
- Jump Desktop has broad permissions (Accessibility, Screen Capture, Mic, Remote Desktop) — expected if in use.
- `~/officina/bin/moneo` had Full Disk Access — revoked, works fine without it (2026-03-17).

## Actions taken
- [x] Enable firewall (2026-03-17)
- [x] FileVault — deliberately OFF for unattended remote reboot (Jump Desktop). Accepted trade-off (2026-03-05)
- [x] Disable Public Folder guest access (2026-03-17)
- [x] Grammarly — Accessibility revoked, app kept (subscription active). Re-grant when needed. (2026-03-17)
- [~] Prune stale TCC entries — skipped, theoretical risk only, binaries don't exist
- [ ] Remove OnVue post-GARP (after 2026-04-04)
