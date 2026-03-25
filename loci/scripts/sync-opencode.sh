#!/bin/bash
# Sync opencode config to agent-config repo

cp ~/.config/opencode/opencode.json ~/agent-config/opencode/
cd ~/agent-config
git add opencode/opencode.json
git commit -m "Update opencode config" && git push

echo "Synced opencode config to agent-config"
