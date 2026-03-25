# claude --print Uses API Credits, Not Max Subscription

ID: ERR-20260314-001

## Problem
`claude --print` (headless/non-interactive mode) ignores Max subscription OAuth and falls back to `ANTHROPIC_API_KEY` when that env var exists. This means headless calls bill against API credits, not your Max20 plan.

Confirmed bug: GitHub #5143, #3040 (closed "Not Planned" Jan 2026, unfixed as of v2.0.76).

## Symptoms
- `claude --print` returns `"Credit balance is too low"` while interactive `claude` works fine
- API console shows negative credit balance
- Affects any tool that shells out to `claude --print`: thalamus, legatus (claude backend), any custom script

## Fix
Strip `ANTHROPIC_API_KEY` from the environment before calling `claude --print`:

```python
# Python
env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "ANTHROPIC_API_KEY")}
subprocess.run(["claude", "--print", "-p", prompt], env=env)
```

```bash
# Shell
env -u CLAUDECODE -u ANTHROPIC_API_KEY claude --print -p "prompt"
```

## Root cause on this machine
`~/.zshenv.tpl` line 7 injects `ANTHROPIC_API_KEY` into every shell session via 1Password. Interactive `claude` uses OAuth (Max subscription). Headless `claude --print` prefers the API key.

## Checklist for any new tool using claude --print
- [ ] Strip both `CLAUDECODE` and `ANTHROPIC_API_KEY` from env
- [ ] Test with `env -u ANTHROPIC_API_KEY claude --print -p "test"` before assuming Max20 billing
