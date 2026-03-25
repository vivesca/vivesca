---
module: CLI Tools
date: 2026-01-26
problem_type: logic_error
component: tooling
symptoms:
  - "Hardcoded 'CORA' references in schema.yaml causing validation failures"
  - "Plugin validation gate required 'valid CORA module' for all users"
  - "Hardcoded filenames (cora-critical-patterns.md) caused file-not-found errors"
root_cause: logic_error
resolution_type: code_fix
severity: high
tags: [hardcoding, portability, open-source, plugin]
---

# Troubleshooting: Hardcoded Project References in Compounding Plugin

## Problem
The `compound-docs` skill and related workflows contained hardcoded references to "CORA" (Every's internal project). This prevented the plugin from being truly project-agnostic, as the YAML validation gate would fail if a user provided a module name not matching the CORA schema.

## Environment
- Module: `compound-engineering-plugin`
- Affected Component: `compound-docs` skill, `schema.yaml`, resolution templates
- Date: 2026-01-26

## Symptoms
- Documentation generation failed during the YAML validation step with error: `module must be a valid CORA module name`.
- Subagents attempted to read non-existent files like `cora-critical-patterns.md`.
- Generated documentation contained "CORA" placeholders instead of project-specific names.

## What Didn't Work
**Direct use of the plugin:**
- **Why it failed:** The plugin was functionally locked to the original internal project name due to strict validation rules in `schema.yaml`.

## Solution
Generalized the plugin by removing all "CORA" references and replacing them with project-agnostic terminology.

**Code changes** (Example from `schema.yaml`):
```yaml
# Before:
module:
  description: "Module/area of CORA (e.g., 'Email Processing')"
validation_rules:
  - "module must be a valid CORA module name"

# After:
module:
  description: "Module/area (e.g., 'Email Processing')"
validation_rules:
  - "module must be a valid module name"
```

**Renamed Components**:
- Renamed `cora-test-reviewer` agent to `test-quality-reviewer`.
- Renamed `cora-critical-patterns.md` reference to `critical-patterns.md`.

**Pull Request**:
- Created PR [#127](https://github.com/EveryInc/compound-engineering-plugin/pull/127) to the upstream repository.

## Why This Works
1. **Root Cause:** Incomplete de-internalization of the plugin code before public release.
2. **Technical fix:** Removing the specific string check in the validation gate and updating templates to use generic terms allows the tool to work in any repository context.

## Prevention
- **Generic Templates**: Always use variables or generic placeholders (e.g., "System", "Module") in shared plugin templates.
- **Validation Flexibility**: Ensure validation rules check for *format* (e.g., non-empty string) rather than specific *values* unless those values are part of a public standard.
- **Global Search Sweep**: Run `grep -ri "<internal-project-name>"` before publishing internal tools to the community.

## Related Issues
- Similar to: [Slow Root Search Performance](./performance-issues/slow-root-search-CLITools-20260126.md) (both addressed CLI/Tooling portability).
