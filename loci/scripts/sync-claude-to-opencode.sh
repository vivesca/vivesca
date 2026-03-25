#!/bin/bash
# Sync entire Claude Code config to OpenCode and Codex
# Usage: sync-claude-to-opencode.sh

set -e

CLAUDE_HOME="$HOME/.claude"
OPENCODE_HOME="$HOME/.config/opencode"
CODEX_HOME="$HOME/.codex"
PLUGIN_TOOL="$HOME/.claude/plugins/marketplaces/every-marketplace"

echo "=== Syncing Claude Code → OpenCode + Codex ==="

# 1. Sync plugins using the converter
echo ""
echo "1. Syncing plugins..."

# Get list of installed plugins from settings.json (source of truth for enablement)
if [ -f "$CLAUDE_HOME/settings.json" ] && [ -f "$CLAUDE_HOME/plugins/installed_plugins.json" ]; then
    ENABLED_PLUGINS=$(cat "$CLAUDE_HOME/settings.json" | jq -r '.enabledPlugins | to_entries[] | select(.value == true) | .key')
    
    for plugin_id in $ENABLED_PLUGINS; do
        # Find the install path from installed_plugins.json
        plugin_path=$(cat "$CLAUDE_HOME/plugins/installed_plugins.json" | jq -r --arg id "$plugin_id" '.plugins[$id][0].installPath // empty')
        
        if [ -n "$plugin_path" ] && [ -d "$plugin_path" ] && [ -f "$plugin_path/.claude-plugin/plugin.json" ]; then
            plugin_name=$(basename "$plugin_path")
            echo "   Converting plugin: $plugin_name ($plugin_id)"
            
            # Backup existing opencode.json if it exists, to merge it later
            [ -f "$OPENCODE_HOME/opencode.json" ] && cp "$OPENCODE_HOME/opencode.json" "$OPENCODE_HOME/opencode.json.tmp"
            
            cd "$PLUGIN_TOOL"
            # Convert to both OpenCode and Codex
            bun run src/index.ts convert "$plugin_path" --to opencode --also codex -o "$OPENCODE_HOME" --codex-home "$CODEX_HOME" 2>/dev/null || echo "   Warning: Failed to convert $plugin_name"
            
            # Merge back the commands and mcp servers if we had a backup
            if [ -f "$OPENCODE_HOME/opencode.json.tmp" ]; then
                NEW_CONFIG=$(cat "$OPENCODE_HOME/opencode.json")
                MERGED=$(jq -s '.[0] * .[1]' "$OPENCODE_HOME/opencode.json.tmp" "$OPENCODE_HOME/opencode.json")
                echo "$MERGED" > "$OPENCODE_HOME/opencode.json"
                rm "$OPENCODE_HOME/opencode.json.tmp"
            fi
        fi
    done
else
    echo "   Required config files not found"
fi

# 2. Sync personal skills (symlink to both)
echo ""
echo "2. Syncing personal skills..."

mkdir -p "$OPENCODE_HOME/skills"
mkdir -p "$CODEX_HOME/skills"

for skill_dir in "$CLAUDE_HOME/skills/"*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")

        # Sync to OpenCode
        target="$OPENCODE_HOME/skills/$skill_name"
        if [ -L "$target" ]; then
            existing=$(readlink "$target")
            if [ "$existing" != "$skill_dir" ] && [ "$existing" != "${skill_dir%/}" ]; then
                rm "$target"
                ln -s "${skill_dir%/}" "$target"
                echo "   OpenCode: $skill_name"
            fi
        elif [ ! -d "$target" ]; then
            ln -s "${skill_dir%/}" "$target"
            echo "   OpenCode: $skill_name"
        fi

        # Sync to Codex
        target="$CODEX_HOME/skills/$skill_name"
        if [ -L "$target" ]; then
            existing=$(readlink "$target")
            if [ "$existing" != "$skill_dir" ] && [ "$existing" != "${skill_dir%/}" ]; then
                rm "$target"
                ln -s "${skill_dir%/}" "$target"
                echo "   Codex: $skill_name"
            fi
        elif [ ! -d "$target" ]; then
            ln -s "${skill_dir%/}" "$target"
            echo "   Codex: $skill_name"
        fi
    fi
done

# 3. Sync MCP servers from settings.json
echo ""
echo "3. Syncing MCP servers..."

if [ -f "$CLAUDE_HOME/settings.json" ]; then
    CLAUDE_MCP=$(cat "$CLAUDE_HOME/settings.json" | jq '.mcpServers // {}')

    if [ "$CLAUDE_MCP" != "{}" ] && [ "$CLAUDE_MCP" != "null" ]; then
        # === OpenCode (JSON format) ===
        OPENCODE_MCP=$(echo "$CLAUDE_MCP" | jq 'to_entries | map({
            key: .key,
            value: {
                type: "local",
                command: ([.value.command] + (.value.args // [])),
                environment: (.value.env // {}),
                enabled: true
            }
        }) | from_entries')

        if [ -f "$OPENCODE_HOME/opencode.json" ]; then
            EXISTING=$(cat "$OPENCODE_HOME/opencode.json")
            MERGED=$(echo "$EXISTING" | jq --argjson new_mcp "$OPENCODE_MCP" '.mcp = (.mcp // {}) + $new_mcp')
            echo "$MERGED" > "$OPENCODE_HOME/opencode.json"
            echo "   OpenCode: merged MCP servers"
        fi

        # === Codex (TOML format) ===
        CODEX_CONFIG="$CODEX_HOME/config.toml"

        # Generate MCP section in TOML
        MCP_TOML=$(echo "$CLAUDE_MCP" | jq -r 'to_entries[] |
            "[mcp_servers.\(.key)]",
            "command = \"\(.value.command)\"",
            (if .value.args and (.value.args | length) > 0 then
                "args = [\(.value.args | map("\"" + . + "\"") | join(", "))]"
            else empty end),
            (if .value.env and (.value.env | length) > 0 then
                "", "[mcp_servers.\(.key).env]",
                (.value.env | to_entries[] | "\(.key) = \"\(.value)\"")
            else empty end),
            ""')

        # Check if config.toml exists and has content
        if [ -f "$CODEX_CONFIG" ]; then
            # Remove existing mcp_servers sections and append new ones
            # Simple approach: check if our MCP servers are already there
            if ! grep -q "^\[mcp_servers\." "$CODEX_CONFIG" 2>/dev/null; then
                echo "" >> "$CODEX_CONFIG"
                echo "# MCP servers synced from Claude Code" >> "$CODEX_CONFIG"
                echo "$MCP_TOML" >> "$CODEX_CONFIG"
                echo "   Codex: appended MCP servers to config.toml"
            else
                echo "   Codex: MCP servers already in config.toml"
            fi
        else
            # Create new config.toml
            echo "# Codex config - synced from Claude Code" > "$CODEX_CONFIG"
            echo "" >> "$CODEX_CONFIG"
            echo "$MCP_TOML" >> "$CODEX_CONFIG"
            echo "   Codex: created config.toml with MCP servers"
        fi
    else
        echo "   No MCP servers in settings.json"
    fi
else
    echo "   No settings.json found"
fi

# 4. Sync AGENTS.md (Codex reads this for instructions)
echo ""
echo "4. Syncing AGENTS.md..."

# Link global CLAUDE.md to Codex AGENTS.md if it exists
if [ -f "$HOME/CLAUDE.md" ]; then
    if [ ! -f "$CODEX_HOME/AGENTS.md" ] && [ ! -L "$CODEX_HOME/AGENTS.md" ]; then
        ln -s "$HOME/CLAUDE.md" "$CODEX_HOME/AGENTS.md"
        echo "   Linked ~/CLAUDE.md → ~/.codex/AGENTS.md"
    else
        echo "   AGENTS.md already exists"
    fi
else
    echo "   No global CLAUDE.md found"
fi

# 5. Summary
echo ""
echo "=== Sync complete ==="
echo ""
echo "OpenCode (~/.config/opencode):"
echo "  Skills: $(ls -d "$OPENCODE_HOME/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "  Agents: $(ls "$OPENCODE_HOME/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "  MCP: $(cat "$OPENCODE_HOME/opencode.json" 2>/dev/null | jq -r '.mcp | keys | length' || echo 0)"
echo ""
echo "Codex (~/.codex):"
echo "  Skills: $(ls -d "$CODEX_HOME/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "  MCP: $(grep -c '^\[mcp_servers\.' "$CODEX_HOME/config.toml" 2>/dev/null || echo 0)"
echo "  AGENTS.md: $([ -f "$CODEX_HOME/AGENTS.md" ] && echo "yes" || echo "no")"
