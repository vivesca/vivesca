---
name: ectodomain
description: Design a CLI interface. Use when building a new CLI, reviewing an existing one, or deciding CLI vs MCP as a tool surface. Covers both human-facing and agent-facing design. Triggers "design a CLI", "new CLI", "CLI best practices", "CLI vs MCP", "review this CLI".
user_invocable: false
epistemics: [cli-design, container-design, delegation-theory]
---

# ectodomain

The CLI is the externally-facing surface of a tool — its "ectodomain." What the shape allows, external callers (humans, agents) bind to. Poor ectodomain design = no productive binding regardless of internal quality.

Read `~/epigenome/chromatin/euchromatin/epistemics/cli-design.md` for the full principles library (clig.dev, 12-Factor CLI, Heroku style guide, agent-facing deltas). This skill is the action wrapper that sits on top.

## Step 1 — Should this be a CLI at all?

Run the four-step decision tree from `genome.md`:

1. **Intermediate data too large for main agent context?** → subagent / nested-LLM MCP (rare, <5%)
2. **Cross-invocation mutable state not on filesystem?** → MCP
3. **Nested/structured input schema** (nested objects, arrays of records)? → MCP
4. **Otherwise** → CLI + skill

Tiebreaker: CLI wraps into MCP cheaply (`subprocess.run` behind `@mcp.tool`). MCP does not unwrap into CLI. When unsure, pick the reversible direction — CLI.

## Step 2 — Identify the audience mix

Every vivesca CLI has two callers: Terry (human, on Blink over SSH) and agents (CC, Codex, ribosome, sortase, gemini-cli). Neither is optional. Design for both:

- Default output is human-pretty (tables, colour when stdout is a TTY).
- `--json` flag emits machine-parseable output. Stable schema, never reorder keys.
- No interactive prompts without a non-interactive override (`--yes`, `--force`, env var).
- Respect `NO_COLOR`. Detect non-TTY stdout and drop colour automatically.
- Typo-tolerance: Terry types on Blink with high error rate — suggest nearest subcommand on unknown input.

## Step 3 — Structure

- **Noun-verb subcommands.** `tool resource action`. Max three levels of nesting.
- **Flat argv.** Nested input = file path or stdin, never JSON on argv. If the natural shape is nested argv, you wanted MCP — go back to step 1.
- **Stable exit codes with documented taxonomy.** `0` ok, `1` generic error, `2` usage error, plus domain-specific codes. Document them in `--help` or a `doctor` subcommand.
- **stdout = data, stderr = logs/errors.** Exit code carries success/failure. This discipline is what makes pipes work.
- **Config precedence.** Flags > env vars > config file > defaults. Document the order.

## Step 4 — Eliminate human-in-the-loop before designing around it

For any step that would block waiting for human input, first ask: can it be removed entirely?

| Human step | Elimination path |
|------------|------------------|
| OTP / SMS code | Session persistence → auth once, reuse indefinitely |
| 2FA password | Keychain (1Password Agents vault, macOS Keychain) |
| OAuth browser flow | Service account, API key, long-lived token |
| Manual approval | `--yes` flag with documented safe-use criteria |
| Copy-paste between tools | Pipe directly, or write to a file the next command reads |
| CAPTCHA | API instead of scrape; if no API, escalate to stealth browser |

**The goal is zero recurring human steps.** One-time setup (initial auth, keychain seeding) is acceptable. Recurring human input per operation is a design flaw — fix the design, don't add a prompt.

## Step 5 — Split at every unavoidable HITL point

If a step genuinely requires a human (first-time SMS code, physical security key), it must be a separate subcommand, not a blocking prompt:

```
tool auth-start <args>     # triggers external action, persists state, prints next command
tool auth-finish <secret>  # reads state, completes with human-provided value
```

State persisted between steps must include **everything** needed to resume: parameters, nonces, server/region/DC if it can migrate, session keys. More than you think.

## Step 6 — Errors tell the agent what to run next

```
# Wrong
Error: not authenticated

# Right
Error: not authenticated. Run: tool auth-start +<phone>
```

Agents read errors and act on them. Errors are control flow, not decoration. Keep error strings stable — agents grep them; drift breaks workflows silently.

## Step 7 — Idempotency by default

- `auth`: already signed in → print "already signed in", exit 0
- `create`: already exists → print current state, exit 0 (or documented non-zero if loud failure is wanted)
- `start`: already running → no-op
- Safe retry is the default. Loud failure is opt-in and documented.

## Step 8 — Self-description

- `--help` is the API contract. Every subcommand, every flag, at least one example per subcommand. Agents read it to self-discover capabilities.
- Consider a `tool schema` subcommand that emits JSON describing commands, flags, exit codes. Agents consume it directly.
- `tool doctor` for self-diagnosis. Exits non-zero if any check fails. Cheap to add, high signal.

## Implementation stacks

| Language | Framework | Used by |
|----------|-----------|---------|
| Python | **Typer** (Click with type hints) | default for new organism work |
| Go | **Cobra + Viper** | kubectl, gh, hugo |
| Rust | **clap** (derive API) | ripgrep, uv, ruff |

Pick the language first; the framework is that language's default. Don't hand-roll argv parsing — every hand-rolled parser eventually fails on `--flag=value` vs `--flag value` or `--`-terminated argv.

## Pre-ship checklist

- [ ] CLI vs MCP decision tree run; CLI is the correct answer
- [ ] `--help` on every subcommand, with at least one example each
- [ ] `--json` output mode for data-returning commands, stable schema
- [ ] `--yes` / `--force` override for every interactive step
- [ ] No blocking stdin reads (`/dev/tty`, bare `read_line`) unless wrapped in a TTY check
- [ ] Errors tell the next command to run when there is one; error strings stable
- [ ] Exit codes documented (help text or `doctor` subcommand)
- [ ] Idempotent where possible; loud-failure documented where not
- [ ] stdout vs stderr discipline verified (pipe through `jq`, does it work?)
- [ ] `NO_COLOR` honoured; non-TTY detection drops colour automatically
- [ ] `assays/test_*.py` present with invocation + `--help` + one happy path (genome: no test = not done)
- [ ] If it's an organism CLI: listed in `~/germline/effectors/` with executable bit, synced via mitosis

## See also

- `~/epigenome/chromatin/euchromatin/epistemics/cli-design.md` — full principles library (clig.dev, 12-Factor, Heroku, agent deltas, anti-patterns)
- `container-design` skill — choosing tool / skill / agent as a capability wrapper
- `organogenesis` skill — designing the skill layer that wraps a CLI
- `~/docs/solutions/grammers-mtproto-agent-auth.md` — worked example: Telegram auth as a two-step agent CLI (DC migration, raw TL calls, SRP 2FA)
