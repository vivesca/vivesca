---
title: macOS Keychain access from CLI tools
tags: [macos, keychain, security-framework, gotcha]
---

# macOS Keychain: use `security` CLI, not Rust/Swift crates

**Problem:** The Rust `security-framework` crate (and likely Swift's Security framework from CLI context) gets SIGKILL'd by macOS when accessing Keychain from non-interactive processes. 60+ zombie processes accumulated from usus-watch LaunchAgent.

**Fix:** Use the `security` CLI command via subprocess:
```
security find-generic-password -s "SERVICE_NAME" -w
```

This works reliably from: terminal, LaunchAgents, Claude Code sandbox, Python subprocess, any context.

**Root cause:** Likely TCC (Transparency, Consent, Control) or codesigning — unsigned binaries using the Security framework directly get killed. The `security` CLI binary is Apple-signed and has the right entitlements.

**Rule:** For any macOS tool that needs Keychain access, always use the `security` CLI via subprocess. Never use native Keychain APIs from CLI tools.

**Discovered:** 2026-03-20. usus Rust → Python rewrite.
