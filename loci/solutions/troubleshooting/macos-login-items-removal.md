---
title: Removing Hidden macOS Login Items (AutoGLM, Comet)
category: troubleshooting
date: 2026-01-26
tags: [macos, startup, login-items, automation, troubleshooting]
---

# Removing Hidden macOS Login Items (AutoGLM, Comet)

## Problem

Unwanted applications (AutoGLM and Comet) were launching automatically on system startup. Standard investigation methods failed to locate the source of these launches.

## Investigation Path

The following locations were checked but contained no references to the unwanted items:

- **LaunchAgents & LaunchDaemons:**
  - `~/Library/LaunchAgents`
  - `/Library/LaunchAgents`
  - `/Library/LaunchDaemons`
  - `/System/Library/LaunchAgents`
  - `/System/Library/LaunchDaemons`
- **Shell Configurations:**
  - `~/.zshrc`
  - `~/.bashrc`
  - `~/.profile`
  - `/etc/zshrc`
  - `/etc/profile`
- **Other:**
  - `crontab -l`
  - System Settings > General > Login Items (Visual check sometimes misses items or doesn't allow easy scripted removal)

## Solution

The items were identified as legacy "Login Items" managed by the macOS `System Events` framework, which are separate from `launchd` agents. These can be managed via AppleScript (`osascript`).

### 1. List All Login Items

Use this command to see the names of all items registered to launch at login:

```bash
osascript -e 'tell application "System Events" to get name of every login item'
```

### 2. Remove Specific Login Items

Once the names are identified, they can be deleted individually:

```bash
# Remove AutoGLM
osascript -e 'tell application "System Events" to delete login item "AutoGLM"'

# Remove Comet
osascript -e 'tell application "System Events" to delete login item "Comet"'
```

### 3. Verification

Run the list command again to ensure they are gone:

```bash
osascript -e 'tell application "System Events" to get name of every login item'
```

## Summary

When an application launches on startup but isn't found in `LaunchAgents` or shell configs, check the legacy Login Items list using `osascript`. This is a common hiding spot for applications installed via standard macOS `.dmg` or `.pkg` installers that don't use modern `launchd` services.
