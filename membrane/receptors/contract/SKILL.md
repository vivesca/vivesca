---
name: contract
description: Manage session contracts — upfront acceptance criteria enforced before session ends. Use when starting non-trivial tasks needing hard completion criteria.
user_invocable: true
---

# contract

Manage task contracts — upfront acceptance criteria that the stop-hook enforces before session termination.

## When to use

- Starting any non-trivial task that needs hard completion criteria
- User says "create a contract", "/contract", "set up a contract for this"
- Before delegating a multi-step task where drift is likely

## Contract location

`~/.claude/contracts/<task-name>_CONTRACT.md`

The Stop hook (`contract-check.js`) blocks session termination if any contract file has unchecked `- [ ]` items.

## Commands

### Create

```bash
mkdir -p ~/.claude/contracts
```

Then write `~/.claude/contracts/<task-name>_CONTRACT.md` with the template below. Fill in task-specific criteria before starting work.

### List

```bash
ls ~/.claude/contracts/
grep -l "- \[ \]" ~/.claude/contracts/*.md 2>/dev/null
```

### Clear (task complete)

```bash
rm ~/.claude/contracts/<task-name>_CONTRACT.md
```

## Template

```markdown
# Contract: <task-name>

## Acceptance Criteria
- [ ] <specific criterion 1>
- [ ] <specific criterion 2>

## Tests
- [ ] All tests passing
- [ ] No test files modified

## Verification
- [ ] Manual smoke test passed
- [ ] Screenshot verified (if UI change)
```

## Principles (from @systematicls)

- Define the endpoint *before* starting — agents know how to begin, not how to end
- Tests are the gold standard: deterministic, unforgeable
- Screenshots for UI work: let the agent iterate until visual output matches intent
- One contract per session — mixing contracts causes context drift

## Triggers

- contract
- session contract
- acceptance criteria
- contract terms
