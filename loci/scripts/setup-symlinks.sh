#!/bin/bash
# Setup symlinks for agent-config

set -e

CONFIG_DIR="$HOME/agent-config"

echo "Setting up agent-config symlinks..."

# Claude Code
if [ -f "$CONFIG_DIR/claude/CLAUDE.md" ]; then
    if [ -L "$HOME/CLAUDE.md" ]; then
        rm "$HOME/CLAUDE.md"
    elif [ -f "$HOME/CLAUDE.md" ]; then
        mv "$HOME/CLAUDE.md" "$HOME/CLAUDE.md.backup"
        echo "Backed up existing ~/CLAUDE.md"
    fi
    ln -s "$CONFIG_DIR/claude/CLAUDE.md" "$HOME/CLAUDE.md"
    echo "✓ Linked CLAUDE.md"
fi

# Claude Code config (.claude.json) — copy, don't symlink (has runtime state)
if [ -f "$CONFIG_DIR/claude/claude.json" ] && [ ! -f "$HOME/.claude.json" ]; then
    cp "$CONFIG_DIR/claude/claude.json" "$HOME/.claude.json"
    echo "✓ Copied .claude.json (template — edit locally as needed)"
elif [ -f "$HOME/.claude.json" ]; then
    echo "· Skipped .claude.json (already exists)"
fi

# Claude Code hooks (~/.claude/hooks/)
if [ -d "$CONFIG_DIR/claude/hooks" ]; then
    mkdir -p "$HOME/.claude"
    if [ -L "$HOME/.claude/hooks" ]; then
        rm "$HOME/.claude/hooks"
    elif [ -d "$HOME/.claude/hooks" ]; then
        mv "$HOME/.claude/hooks" "$HOME/.claude/hooks.backup"
        echo "Backed up existing ~/.claude/hooks/"
    fi
    ln -s "$CONFIG_DIR/claude/hooks" "$HOME/.claude/hooks"
    echo "✓ Linked hooks/"
fi

# Claude Code settings (~/.claude/settings.json)
if [ -f "$CONFIG_DIR/claude/settings.json" ]; then
    mkdir -p "$HOME/.claude"
    if [ -L "$HOME/.claude/settings.json" ]; then
        rm "$HOME/.claude/settings.json"
    elif [ -f "$HOME/.claude/settings.json" ]; then
        mv "$HOME/.claude/settings.json" "$HOME/.claude/settings.json.backup"
        echo "Backed up existing ~/.claude/settings.json"
    fi
    ln -s "$CONFIG_DIR/claude/settings.json" "$HOME/.claude/settings.json"
    echo "✓ Linked settings.json"
fi

# OpenCode
if [ -f "$CONFIG_DIR/opencode/opencode.json" ]; then
    mkdir -p "$HOME/.config/opencode"
    if [ -f "$HOME/.config/opencode/opencode.json" ] && [ ! -L "$HOME/.config/opencode/opencode.json" ]; then
        mv "$HOME/.config/opencode/opencode.json" "$HOME/.config/opencode/opencode.json.backup"
        echo "Backed up existing opencode.json"
    fi
    ln -sf "$CONFIG_DIR/opencode/opencode.json" "$HOME/.config/opencode/opencode.json"
    echo "✓ Linked opencode.json"
fi

echo "Done! Restart your AI agents to load the new configuration."
