#!/bin/bash
# Removes irrelevant CE plugin agents, skills, and commands from Claude Code cache.
# Idempotent — safe to run repeatedly. Items reappear on plugin update,
# so this runs on shell startup via .zshrc.
#
# To modify exclusion lists, edit the arrays below.

CE_BASE="$HOME/.claude/plugins/cache/every-marketplace/compound-engineering"
removed=0

# --- AGENTS TO REMOVE (relative to agents/) ---
EXCLUDE_AGENTS=(
  review/kieran-rails-reviewer.md
  review/dhh-rails-reviewer.md
  review/schema-drift-detector.md
  review/data-migration-expert.md
  review/deployment-verification-agent.md
  review/data-integrity-guardian.md
  review/julik-frontend-races-reviewer.md
  design/figma-design-sync.md
  design/design-implementation-reviewer.md
  design/design-iterator.md
  docs/ankane-readme-writer.md
  workflow/lint.md
  workflow/every-style-editor.md
  workflow/spec-flow-analyzer.md
  workflow/bug-reproduction-validator.md
  workflow/agent-browser.md
  workflow/brainstorming.md
  docs/compound-docs.md
  workflow/dspy-ruby.md
  workflow/file-todos.md
  design/frontend-design.md
  design/gemini-imagegen.md
  workflow/skill-architect.md
)

# --- COMMANDS TO REMOVE (relative to commands/) ---
# Keep: lfg.md, slfg.md, workflows/, deepen-plan.md, plan_review.md, reproduce-bug.md
EXCLUDE_COMMANDS=(
  agent-native-audit.md
  changelog.md
  create-agent-skill.md
  deploy-docs.md
  feature-video.md
  generate_command.md
  heal-skill.md
  release-docs.md
  report-bug.md
  resolve_parallel.md
  resolve_pr_parallel.md
  resolve_todo_parallel.md
  test-browser.md
  triage.md
  xcode-test.md
)

# --- SKILLS TO REMOVE (directory names under skills/) ---
# Keep: git-worktree
EXCLUDE_SKILLS=(
  agent-browser
  agent-native-architecture
  andrew-kane-gem-writer
  brainstorming
  compound-docs
  create-agent-skills
  dhh-rails-style
  dspy-ruby
  every-style-editor
  file-todos
  frontend-design
  gemini-imagegen
  orchestrating-swarms
  rclone
  skill-creator
)

for ver in "$CE_BASE"/*/; do
  [ -d "$ver" ] || continue

  # Remove agents
  for agent in "${EXCLUDE_AGENTS[@]}"; do
    f="${ver}agents/${agent}"
    if [ -f "$f" ]; then
      rm "$f"
      ((removed++))
    fi
  done

  # Remove commands
  for cmd in "${EXCLUDE_COMMANDS[@]}"; do
    f="${ver}commands/${cmd}"
    if [ -f "$f" ]; then
      rm "$f"
      ((removed++))
    fi
  done

  # Remove skills (directories)
  for skill in "${EXCLUDE_SKILLS[@]}"; do
    d="${ver}skills/${skill}"
    if [ -d "$d" ]; then
      rm -rf "$d"
      ((removed++))
    fi
  done
done

[ $removed -gt 0 ] && echo "[ce-trim] Removed $removed irrelevant CE items (agents/commands/skills)"

# --- PURGE STALE TODO FILES ---
todo_purged=$(/usr/bin/find "$HOME/.claude/todos" -name "*.json" -mtime +7 2>/dev/null | wc -l | tr -d ' ')
if [ "$todo_purged" -gt 0 ] 2>/dev/null; then
  /usr/bin/find "$HOME/.claude/todos" -name "*.json" -mtime +7 -delete 2>/dev/null
  echo "[ce-trim] Purged $todo_purged stale todo files"
fi

exit 0
