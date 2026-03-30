---
name: chaperone
description: Propagate code changes to skills, memories, and routing after implementation.
user_invocable: false
---

# chaperone -- fold new code into the system

After building or modifying a tool, enzyme, organelle, or effector, ensure the change propagates to all dependent layers. Code that exists but isn't reflected in skills/memories is invisible to future sessions.

## When to fire

- After any code change to a tool, enzyme, organelle, or effector
- After renaming anything
- After adding a new capability
- At the end of a building session before wrapping up

## Checklist

Run through these after implementation work. Skip items that don't apply.

### 1. Skill update

Does a skill use or reference the changed component?

```bash
grep -rl "COMPONENT_NAME" ~/germline/membrane/receptors/*/SKILL.md
```

If yes:
- Update the skill's description of what the tool does
- Update allowed-tools if a new tool was added
- Update the probe/routing sequence if behavior changed
- Update trigger phrases if the scope expanded

If a new tool has no corresponding skill and requires LLM judgment to use correctly, create one. If it's purely deterministic, no skill needed.

### 2. Memory update

Does a memory reference the changed component?

```bash
grep -rl "COMPONENT_NAME" ~/.claude/projects/-Users-terry/memory/
```

If yes, update the memory to reflect the new behavior. If a memory is now wrong, fix or remove it.

If the change introduces a retrieval pattern future sessions need (e.g. "where does X log to?"), save a reference memory.

### 3. Routing update

If a new tool was added to an existing domain:
- Check if the relevant skill's routing table includes it
- Check if ecphory or other dispatch skills know about it

If a tool was renamed:
- Sweep all skills for old name: `grep -rl "OLD_NAME" ~/germline/membrane/receptors/`
- Sweep hooks: `grep -rl "OLD_NAME" ~/germline/membrane/cytoskeleton/`
- Sweep synapse.py references

### 4. Reference sweep (rename only)

After renaming:

```bash
grep -r "OLD_NAME" ~/germline/ --include="*.py" --include="*.md" | grep -v __pycache__ | grep -v .archive
```

Update all live references. Archived files can be left.

### 5. Three-layer check

Per genome: every non-trivial capability ships as three layers.

- **MCP tool** (structured interface) -- does it exist?
- **Skill** (judgment layer) -- does it need one?
- **Organelle or CLI** (deterministic execution) -- is the logic in code, not prompts?

If a layer is missing and should exist, flag it. If a layer is intentionally omitted, that's fine.

## Anti-patterns

- Building a tool and not updating the skill that dispatches to it (tool is invisible)
- Renaming a component and missing references in skills/hooks (silent breakage)
- Adding a memory about how to use a tool instead of updating the skill (memories decay, skills persist)
- Updating code but not the skill description (LLM uses stale instructions)
