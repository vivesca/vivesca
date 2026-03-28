#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="/Users/terry/.codex/skills/.system/skill-installer/scripts"
INSTALLER="${SCRIPT_DIR}/install-skill-from-github.py"

SKILLS=(
  agent-browser
  agent-native-architecture
  andrew-kane-gem-writer
  ce-brainstorm
  dhh-rails-style
  dspy-ruby
  every-style-editor
  frontend-design
  gemini-imagegen
  git-worktree
  rclone
)
# Removed from SKILLS (2026-03-27): compound-docs and file-todos were renamed/removed
# upstream in EveryInc/compound-engineering-plugin. Local installs preserved.

REPO="EveryInc/compound-engineering-plugin"
BASE_PATH="plugins/compound-engineering/skills"
CODEX_SKILLS_DIR="/Users/terry/.codex/skills"

BACKUP_DIR="/Users/terry/.codex/skills-backup/compound-engineering-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"

restore_backup() {
  for skill in "${SKILLS[@]}"; do
    if [ -d "${BACKUP_DIR}/${skill}" ] && [ ! -d "${CODEX_SKILLS_DIR}/${skill}" ]; then
      mv "${BACKUP_DIR}/${skill}" "${CODEX_SKILLS_DIR}/${skill}"
    fi
  done
}

cleanup_partial_installs() {
  for skill in "${SKILLS[@]}"; do
    if [ -d "${CODEX_SKILLS_DIR}/${skill}" ] && [ ! -d "${BACKUP_DIR}/${skill}" ]; then
      rm -rf "${CODEX_SKILLS_DIR:?}/${skill}"
    fi
  done
}

trap 'cleanup_partial_installs; restore_backup' ERR

for skill in "${SKILLS[@]}"; do
  if [ -d "${CODEX_SKILLS_DIR}/${skill}" ]; then
    mv "${CODEX_SKILLS_DIR}/${skill}" "${BACKUP_DIR}/"
  fi
done

python3 "${INSTALLER}" \
  --repo "${REPO}" \
  --path \
  ${BASE_PATH}/agent-browser \
  ${BASE_PATH}/agent-native-architecture \
  ${BASE_PATH}/andrew-kane-gem-writer \
  ${BASE_PATH}/ce-brainstorm \
  ${BASE_PATH}/dhh-rails-style \
  ${BASE_PATH}/dspy-ruby \
  ${BASE_PATH}/every-style-editor \
  ${BASE_PATH}/frontend-design \
  ${BASE_PATH}/gemini-imagegen \
  ${BASE_PATH}/git-worktree \
  ${BASE_PATH}/rclone

exit 0
