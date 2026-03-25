---
module: System
date: 2026-01-26
problem_type: developer_experience
component: documentation
symptoms:
  - "Need for robust backup of technical documentation"
  - "Desire to integrate technical solutions with personal Obsidian vault"
root_cause: incomplete_setup
resolution_type: workflow_improvement
severity: low
tags: [obsidian, symlinks, documentation, workflow, backup]
---

# Integrating Technical Docs into Obsidian Vault

## Problem Statement
The user wanted to ensure their growing technical knowledge base (`docs/solutions`, `plans`, etc.) was both version-controlled/backed up and easily accessible within their existing Obsidian-based personal knowledge management system.

## Findings
- **Location**: Technical documentation was being created in `~/docs/` at the system root.
- **Constraint**: While the root directory was not a git repo, the user's Obsidian vault (`~/code/epigenome/chromatin`) already had an established git backup and versioning workflow.
- **Requirement**: Maintain compatibility with CLI tools and agents that expect `~/docs` to be a valid path.

## Proposed Solutions

### Option 1: Symlink Integration (Selected)
Move the physical files into the version-controlled vault and provide a symbolic link at the expected root location. This solves for backup, discoverability in Obsidian, and CLI compatibility simultaneously.

**Implementation**:
```bash
# 1. Create target structure in vault
mkdir -p ~/code/epigenome/chromatin/Technical

# 2. Move existing docs directory
mv ~/docs ~/code/epigenome/chromatin/Technical/docs

# 3. Create symlink back to root
ln -s ~/code/epigenome/chromatin/Technical/docs ~/docs
```

## Recommended Action
Use the symlink pattern for any specialized data directory that needs to be "anchored" at a specific path for system/agent use but belongs conceptually (and for backup purposes) within a personal knowledge vault.

## Technical Details
- **Affected Path**: `~/docs` (now a symlink)
- **Target Path**: `~/code/epigenome/chromatin/Technical/docs` (physical storage)
- **Git Context**: Now automatically tracked by the vault's `.git` repository.

## Prevention
- Standardize on `~/code/epigenome/chromatin` as the single source of truth for all "knowledge" assets.
- Use symlinks to bridge the gap between "conceptually centralized" storage and "physically required" paths.

## Related Issues
- See also: [gemini-3-flash-high-config-CLI-20260126.md](./gemini-3-flash-high-config-CLI-20260126.md)
