---
name: Obsidian Vault Rename & Wikilink Update Tools
description: CLI tools, libraries, and scripts for renaming files in Obsidian/wikilink-based markdown vaults and updating all references, without requiring the Obsidian app
type: reference
---

## Key finding
No single headless CLI fully handles all four edge cases (plain wikilinks, aliases, heading links, display text) with documented proof. Best bets are notesmd-cli (Go CLI, headless confirmed) and turbovault-batch (Rust library, UpdateLinks + MoveNote documented).

## Tier 1 — Headless, dedicated rename + link update

### notesmd-cli (yakitrak/notesmd-cli)
- Language: Go
- Headless: YES — explicitly documented, "Obsidian does not need to be running"
- Rename/move: `notesmd move "old.md" "new.md"` — "all links inside vault are updated"
- Edge case coverage: NOT documented in README. Basic [[note]] confirmed; aliases/headings/display text unverified.
- Install: `brew install yakitrak/yakitrak/notesmd-cli` or direct binary
- Repo: https://github.com/Yakitrak/notesmd-cli

### turbovault (Epistates/turbovault)
- Language: Rust workspace; MCP server + SDK
- Headless: YES — runs as local server, no Obsidian app required
- Rename/move: `MoveNote` batch operation; `UpdateLinks` changes old targets to new targets
- Edge case coverage: turbovault-parser claims full Obsidian wikilink syntax: `[[note]]`, `[[note|alias]]`, `[[note#section]]`, `[[note#^block]]`
- Crates: turbovault-parser, turbovault-batch, turbovault-graph
- Primary use case: MCP server for AI agents, but also usable as Rust library
- Repo: https://github.com/Epistates/turbovault

## Tier 2 — Requires Obsidian running

### Official Obsidian CLI (v1.12.4, Feb 2026)
- Headless: NO — requires Obsidian app running (will auto-launch it)
- Auto-launch behavior: CLI IS both CLI and app launcher. If app is closed, running any `obsidian` command launches the FULL GUI — does not return, blocks the terminal. Confirmed across multiple forum threads.
- Rename: `obsidian move file=Old to="Archive/Old.md"` or `obsidian rename` (added v1.12.2)
- Wikilink update: YES — goes through Obsidian's internal API so gets correct resolution
- Edge cases: YES — full Obsidian-native link updating
- Limitation: Desktop only, sequential (slow on bulk operations), Windows Unicode issues in early versions
- CLI re-registration bug: on macOS, after quitting and relaunching Obsidian, CLI may require re-registration (Settings → General → Register CLI). Root cause: outdated installer version.
- Source: https://dev.to/shimo4228/obsidians-official-cli-is-here-no-more-hacking-your-vault-from-the-back-door-3123
- Forum thread (auto-launch + re-registration): https://forum.obsidian.md/t/cli-stops-working-after-obsidian-quit-relaunch-on-macos-requires-re-registration/111419
- Forum thread (CLI launches GUI): https://forum.obsidian.md/t/cli-behaviour-is-inconsistent/111948

### Workarounds for "app must be running" constraint

#### Option A — obsidian-tray plugin (community, abandoned)
- Plugin hides Obsidian to macOS menubar instead of quitting; keeps app alive without visible window
- Status: ABANDONED. Last release v0.3.5 Sep 2023, 33 open issues, no recent activity
- Repo: https://github.com/dragonwocky/obsidian-tray
- NOT recommended for production use

#### Option B — LaunchAgent + `open --background`
- Launch Obsidian silently at login:
  `open --background -a /Applications/Obsidian.app`
  then hide it: `osascript -e 'tell application "System Events" to set visible of application process "Obsidian" to false'`
- Keeps app alive in background; CLI commands then work
- Window re-appears whenever CLI triggers a command (Obsidian brings itself to focus on some commands)
- No community-tested plist template found for this specific use case

#### Option C — obsidian-headless (obsidianmd/obsidian-headless, Feb 2026)
- SCOPE: Obsidian Sync ONLY — not vault operations (no rename/move/backlinks)
- Install: `npm install -g obsidian-headless` (Node.js 22+)
- Commands: `ob login`, `ob sync`, `ob sync --continuous`, `ob sync-list-remote`, etc.
- True daemon: runs without GUI, keeps vault synced. No CLI vault ops.
- Requires: Obsidian Sync subscription
- Repo: https://github.com/obsidianmd/obsidian-headless
- Changelog: https://obsidian.md/changelog/2026-02-27-sync/

## Electron / `--headless` flag status
- No `--no-window` or `--headless` Electron flag confirmed for Obsidian macOS
- `--ozone-platform=headless` works on Linux only (prevents segfault with no display), not macOS
- No community-documented Chromium headless flag that works with Obsidian on macOS

## Tier 3 — Analysis only (no rename)

### obsidiantools (Python)
- Headless: YES — reads vault directly
- Rename: NO — analysis/graph only
- Graph API: NetworkX graph, get_backlinks(), backlinks_index — useful for building your own rename tool
- Repo: https://github.com/mfarragher/obsidiantools

### obsidian-export (Rust crate)
- Purpose: Export vault to standard Markdown
- Rename: NO
- Wikilink parsing: YES — parses [[note]] and ![[note]] embeds
- Useful as: base parser if building custom rename logic
- Crate: https://crates.io/crates/obsidian-export

### turbovault-parser (standalone)
- Purpose: Fast Obsidian markdown parsing
- Claims: `[[Note]]`, `[[folder/Note#Heading]]`, `[[Note#^block]]` parsing
- Rename: NO — parser only
- Crate: https://crates.io/crates/turbovault-parser

## Misinformation flags
- obsidian-metadata (natelandau): does NOT handle wikilinks — metadata/frontmatter only
- obsidiantools: does NOT mutate files — analysis library only
- Foam: handles rename+link-update but ONLY inside VS Code (no headless CLI mode)
- note-link-janitor: adds backlinks at bottom of files, does NOT update forward links on rename

## Search methodology that worked
- Direct GitHub repo fetch > web search for behavioral details
- "headless" + "without obsidian running" as discriminating filter
- crates.io keyword "obsidian" surfaces Rust ecosystem
- turbovault discovered via: "obsidian rust wikilink rename update crates.io"

## Key unverified claims
- notesmd-cli's handling of [[note|display]], [[note#heading]] edge cases: not documented, needs source code check
- turbovault-batch UpdateLinks: "automatic wikilink updates" claimed but full edge case spec not published
