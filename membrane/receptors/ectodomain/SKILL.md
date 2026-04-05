---
name: ectodomain
description: Design a CLI interface. Use when building a new CLI, reviewing an existing one, or deciding CLI vs MCP as a tool surface. Covers human-facing and agent-facing design, with principles verified against clig.dev, Dickey's 12 Factor CLI Apps, Heroku style guide, and joelclaw's agent-CLI writeup. Triggers "design a CLI", "new CLI", "CLI best practices", "CLI vs MCP", "review this CLI".
user_invocable: false
verified_against_primary_sources: 2026-04-05
---

# ectodomain

The CLI is the externally-facing surface of a tool — its "ectodomain." What the shape allows, external callers (humans, agents) bind to. Poor ectodomain design = no productive binding regardless of internal quality.

This skill is both the action walkthrough (Steps 1–8 below) and the verified principles reference. The four canonical sources: **clig.dev**, **Jeff Dickey's 12 Factor CLI Apps** (Medium 2018), **Heroku CLI Style Guide**, **joelclaw.com/cli-design-for-ai-agents**. Primary sources cross-checked 2026-04-05.

---

## Step 1 — Should this be a CLI at all?

Run the four-step decision tree from `genome.md`:

1. **Intermediate data too large for main agent context?** → subagent / nested-LLM MCP (rare, <5%)
2. **Cross-invocation mutable state not on filesystem?** → MCP
3. **Nested/structured input schema** (nested objects, arrays of records)? → MCP
4. **Otherwise** → CLI + skill

Tiebreaker: CLI wraps into MCP cheaply (`subprocess.run` behind `@mcp.tool`). MCP does not unwrap into CLI. When unsure, pick the reversible direction — CLI.

Measurement note: in the CC/Codex/Gemini/Goose stack all clients have shell, so "cross-client distribution" is not a valid MCP criterion — CLIs on PATH are already cross-client. MCP over HTTP earns its keep only for enterprise tooling with centralised OAuth/RBAC/audit (Kong, Pomerium, MintMCP, Strata, Aembit).

## Step 2 — Identify the audience mix and pick an output default

Every vivesca CLI has two callers: Terry (human, on Blink over SSH) and agents (CC, Codex, ribosome, sortase, gemini-cli). Neither is optional. Two viable designs — **pick one deliberately, don't split the difference**:

| Design | When to use | Reference |
|--------|-------------|-----------|
| **Human-pretty default, `--json` opt-in** | Terry is the primary caller; agents tolerate the extra flag. Fit: `hygroreception`, `fasti`, `sopor`, `usage`, most status-read CLIs. | clig.dev / Heroku convention |
| **JSON-default, humans pipe through `jq`** | Agents are the primary caller; Terry reads via `jq` on Blink. Fit: organism infrastructure CLIs (`ribosome`, `sortase`, `transposase`, `endosomal`, `polymerase`). | joelclaw.com/cli-design-for-ai-agents |

Other rules apply to both:
- No interactive prompts without a non-interactive override (`--yes`, `--force`, env var).
- Respect `NO_COLOR`. Detect non-TTY stdout and drop colour automatically.
- Typo-tolerance: Terry types on Blink with high error rate — suggest nearest subcommand on unknown input.
- If JSON-default: envelope should follow the joelclaw HATEOAS pattern — see the schema in the Reference section below.

## Step 3 — Structure

- **Subcommand pattern — pick one separator and stick with it.** Two valid conventions:
  - **Spaces (git/kubectl/docker style):** `tool resource action` — `git remote add`, `kubectl pod logs`. Clean, reads as noun-verb. Default choice for new organism CLIs.
  - **Colons (Heroku/oclif style):** `tool topic:action` — `heroku apps:create`, `heroku config:set`. Preferable when topic-level commands must also accept arguments (space-separated would cause parser ambiguity per Dickey factor 11).
- Max three levels of nesting. Deeper = split into separate tools.
- **Flat argv.** Nested input = file path or stdin, never JSON on argv. If the natural shape is nested argv, you wanted MCP — go back to step 1.
- **Stable exit codes with documented taxonomy.** `0` ok, `1` generic error, `2` usage error, plus domain-specific codes. Document them in `--help` or a `doctor` subcommand.
- **stdout = data, stderr = logs/errors/progress.** Exit code carries success/failure. Even non-error messages (progress bars, spinners, `cli.action()` output) go to stderr so stdout stays clean for piping. This discipline is what makes pipes work.
- **Config precedence.** Flags > env vars > XDG config file > defaults. Document the order. XDG-spec: `$XDG_CONFIG_HOME`/`~/.config/<tool>`, `$XDG_DATA_HOME`/`~/.local/share/<tool>`, `~/.cache/<tool>` (Linux) / `~/Library/Caches/<tool>` (macOS).

## Step 4 — Eliminate human-in-the-loop before designing around it

For any step that would block waiting for human input, first ask: **can it be removed entirely?**

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

## Step 6 — Errors tell the caller what to do next

```
# Wrong
Error: not authenticated

# Right
Error: not authenticated. Run: tool auth-start +<phone>
```

Errors are control flow, not decoration. Keep error strings stable — agents grep them; drift breaks workflows silently. For JSON-default CLIs, errors also carry a `fix` field in plain language plus a `next_actions` list biased toward recovery (joelclaw HATEOAS pattern).

## Step 7 — Idempotency by default

- `auth`: already signed in → print "already signed in", exit 0
- `create`: already exists → print current state, exit 0 (or documented non-zero if loud failure is wanted)
- `start`: already running → no-op
- Safe retry is the default. Loud failure is opt-in and documented.

## Step 8 — Self-description

- `--help` is the API contract. Every subcommand, every flag, at least one example per subcommand. Both humans and agents read it to self-discover.
- Consider a `tool schema` subcommand that emits JSON describing commands, flags, exit codes. Agents consume it directly.
- For JSON-default agent-first CLIs: the bare root command (no args) should return the full command tree as JSON — one call, agent knows everything.
- `tool doctor` for self-diagnosis. Exits non-zero if any check fails. Cheap to add, high signal.

## Pre-ship checklist

- [ ] CLI vs MCP decision tree run; CLI is the correct answer
- [ ] Audience-mix design picked deliberately (human-default or JSON-default, not both)
- [ ] `--help` on every subcommand, with at least one example each
- [ ] `--yes` / `--force` override for every interactive step
- [ ] No blocking stdin reads (`/dev/tty`, bare `read_line`) unless wrapped in a TTY check
- [ ] Errors tell the next command to run when there is one; error strings stable
- [ ] Exit codes documented (help text or `doctor` subcommand)
- [ ] Idempotent where possible; loud-failure documented where not
- [ ] stdout vs stderr discipline verified (pipe through `jq`, does it work?)
- [ ] `NO_COLOR` honoured; non-TTY detection drops colour automatically
- [ ] `assays/test_*.py` present with invocation + `--help` + one happy path (genome: no test = not done)
- [ ] If an organism CLI: listed in `~/germline/effectors/` with executable bit, synced via mitosis

---

## Reference: clig.dev — philosophy

- **Human-first design.** UNIX CLIs were historically designed for other programs. Today most CLIs are used by humans first — design for them first, machines second.
- **Simple parts that work together.** UNIX composability (pipes, stdin/stdout) still matters in the CI/CD and orchestration era, even more than before.
- **Consistency across programs.** Conventions are hardwired into users' fingers. Break with convention only when it demonstrably harms usability, and do so with intention.
- **Saying just enough.** Neither too terse nor too chatty. Novices need more context; power users need less. Both must be served.
- **Ease of discovery.** "See-and-point" and "remember-and-type" aren't mutually exclusive. CLIs can help you learn and remember through comprehensive help, example invocations, suggestions.
- **Conversation as the norm.** Running a program is usually back-and-forth: user tries, gets error, changes command, tries again. Design errors as the other half of a conversation, not as failures.
- **Robustness — both objective and subjective.** Software must *be* robust (handle unexpected input, idempotent ops) AND *feel* robust (responsive, informative, not flimsy).
- **Empathy.** "Giving the user the feeling that you are on their side." Delighting the user = exceeding expectations.
- **Chaos.** The terminal is a mess of inconsistencies, and that mess is also its source of power. Follow conventions most of the time; when you break them, break them with intention and clarity.

## Reference: clig.dev — concrete guidelines

### Help
- Display extensive help on `-h`/`--help`. Every subcommand gets its own.
- Display concise help when `myapp` or `myapp subcommand` is run with required args missing.
- Every help text should include at least one example — the single most-referenced doc.

### Output
- Human-readable output is paramount. Check whether stdout is a TTY; branch on that.
- Have machine-readable output where it doesn't impact usability.
- Display formatted JSON when `--json` is passed (if structured output is meaningful).

### Errors
- **Catch errors and rewrite them for humans.** "Can't write to file.txt. You might need to make it writable by running `chmod +w file.txt`." Errors are documentation.
- **Signal-to-noise ratio is crucial.** Multiple errors of the same type → group under one heading.
- Stack traces are for developers. Show a friendly error; log the full trace to a file.

### Arguments and flags
- **Args** are positional (`cp foo bar`); order often matters.
- **Flags** are named (`-r`/`--recursive`); order doesn't affect semantics.
- **Prefer flags to args** — clearer, more future-proof, easier to autocomplete.
- Standard naming: `-h`/`--help`, `-v`/`--verbose`, `--version`, `-q`/`--quiet`, `-f`/`--force`, `-o`/`--output`, `-n`/`--dry-run`, `-y`/`--yes`.
- Support `--` as pass-through terminator for flags forwarded to another process.

### Interactivity
- **Only prompt if `stdin` is a TTY.** In a pipe/script, throw an error telling the user which flag to pass.
- **If `--no-input` is passed, never prompt.**
- Don't echo passwords as the user types (terminal echo-off).
- Let the user escape. Make it clear how to get out.

### Signals
- On Ctrl-C, exit as soon as possible. Say something immediately, add a timeout to cleanup.
- If Ctrl-C fires during cleanup, skip it. Tell the user what a second Ctrl-C will do, especially for destructive paths (Docker Compose: "Gracefully stopping... (press Ctrl+C again to force)").

### Configuration (three categories)
1. **Varies invocation-to-invocation** (debug level, dry-run) → flags, optionally env vars.
2. **Stable but varies between projects/users** (editor, API endpoint) → env vars or project config file.
3. **Complex structured config** → config file, flags to override.

### Naming
- Simple, memorable, lowercase, short. `curl` good, `DownloadURL` bad.
- Not too generic. ImageMagick and Windows both shipped `convert` and the collision has been painful for decades.
- Dashes only if needed.

### Analytics
- **Do not phone home without explicit consent.** Users will find out.
- Opt-in by default. Opt-out only with clear first-run disclosure and easy disable.

## Reference: 12 Factor CLI Apps (Jeff Dickey, 2018)

**Do not confuse with 12 Factor App** — Dickey borrowed the naming pattern from Heroku's backend app methodology but the twelve factors below are CLI-specific, from his Medium article and the oclif framework.

1. **Great help is essential.** `mycli`, `mycli --help`, `mycli -h`, `mycli help`, `mycli subcommand --help` — all must show help. `-h`/`--help` reserved for help only. Include examples. Shell completion is help.
2. **Prefer flags to args.** 1 arg is fine when obvious (`rm file`); 2 is suspect; 3 never good. Variable-length same-type args are fine (`rm file1 file2 file3`). Accept `--` as pass-through.
3. **What version am I on?** `mycli version`, `mycli --version`, `mycli -V` — all must work. `mycli -v` too unless `-v` is verbose. Include build info for debugging. Send version as `User-Agent` for API-backed CLIs.
4. **Mind the streams.** stdout for data, stderr for messaging (including non-error messages like progress bars — curl puts progress on stderr precisely so you can pipe stdout). If you invoke a subcommand, pipe its stderr up to the user.
5. **Handle things going wrong.** Error messages contain: (1) code, (2) title, (3) optional description, (4) how to fix, (5) URL for more. Have a way to view full debug output via env var (`DEBUG=*`).
6. **Be fancy!** Colours, spinners, progress bars — but fall back to plain when stdout isn't a TTY, when `NO_COLOR` is set, when `TERM=dumb`, or when `--no-color` is passed. Offer app-specific `MYAPP_NOCOLOR` too. ANSI escapes in files or pipes are corruption.
7. **Prompt if you can.** If stdin is a TTY, prompt for missing input rather than erroring. **Never require a prompt** — always allow a flag to bypass for scripting. Confirmation dialogs for dangerous actions (type the app name to confirm deletion).
8. **Use tables.** No borders — each row is a single parseable entry. Support `--columns`, `--no-truncate`, `--no-headers`, `--filter`, `--sort`, and csv/json output. Grep-friendly by default.
9. **Be speedy.** Benchmark with `time mycli`. Targets: <100ms ideal, 100–500ms acceptable, 500ms–2s usable, 2s+ users will avoid. Lazy-load command modules.
10. **Encourage contributions.** Open source, license, CoC, contribution guide, plugins architecture if applicable.
11. **Be clear about subcommands.** Single-command CLIs (`cp`, `grep`) vs multi-command (`git`, `npm`). No-args → multi lists subcommands, single shows help. **Separator:** git uses spaces, Heroku uses colons. Dickey argues colons are preferable because space-separated `heroku domains` can't be both a topic list AND accept args — parser can't distinguish.
12. **Follow XDG-spec.** Config: `$XDG_CONFIG_HOME` or `~/.config/myapp`. Data: `$XDG_DATA_HOME` or `~/.local/share/myapp`. Cache: `~/.cache/myapp` Linux / `~/Library/Caches/myapp` macOS / `%LOCALAPPDATA%\myapp` Windows.

## Reference: Heroku CLI Style Guide

- **Topic and command names** are single lowercase words, no hyphens/underscores/spaces. Kebab-case only if unavoidable (`pg:credentials:repair-default`).
- **Subcommand separator is a colon**, not a space (`heroku apps:create`). Reason: lets `heroku config` (list) coexist with `heroku config:set` (mutate) without parser ambiguity.
- **Never create a `*:list` command.** The bare topic is the list: `heroku config` lists config vars, don't also ship `heroku config:list`.
- **Descriptions are lowercase, no trailing period, fit 80-char screens.**
- **Prefer flags to args.** `heroku fork --from src --to dst`, not `heroku fork src dst`.
- **Prompting:** inquirer-style prompts for missing input, but always accept the flag for scripting.
- **Action commands** (remote work) use a `cli.action()` helper — TTY-aware spinner on stderr, graceful degradation when piped.
- **Grep-parseable output by default.** Each row = one entry, no table borders, column-aligned. `heroku regions | grep tokyo` must work.
- **`--json` flag for machine-readable** when human output isn't enough. `grep` + `jq` is the target.
- **Output on stdout, warnings + errors + `cli.action()` on stderr.**
- **Colours disabled** when stdout isn't a TTY, when `--no-color` is passed, or when `COLOR=false` is set.
- **Dependency hygiene:** no native deps (break on runtime bumps), judicious with transitive deps.

## Reference: Agent-first CLI design (joelclaw / Joel Hooks)

A stronger position than clig.dev/Heroku's "design for humans, support agents via `--json`." Joel's claim: **design for agents first, and humans get a usable tool for free (pipe through `jq`). Design for humans first, and agents get nothing.**

Relevant when the primary caller is an LLM agent and the human is secondary — the case for most vivesca organism CLIs.

### Principle 1: JSON always — not a flag
No plain text, no tables, no ANSI. **No `--json` flag to opt in.** JSON is the default and only format. The agent never has to guess what it's getting. Humans get colour back by piping through `jq`.

### Principle 2: HATEOAS — tell the agent what to do next
Every response includes `next_actions` — command **templates**, not literal commands, with typed placeholders the agent fills in:

```json
{
  "ok": true,
  "command": "joelclaw status",
  "result": { "server": { "ok": true }, "worker": { "ok": true, "functions": 35 } },
  "next_actions": [
    { "command": "joelclaw functions", "description": "View registered functions" },
    {
      "command": "joelclaw runs [--status <status>] [--count <count>]",
      "description": "List recent runs",
      "params": {
        "status": { "enum": ["COMPLETED", "FAILED", "RUNNING", "QUEUED", "CANCELLED"] },
        "count": { "default": 10 }
      }
    }
  ]
}
```

Params metadata: `value` (pre-filled from current response), `default` (if omitted), `enum` (closed-set choices — no hallucination), `description` (semantics). Errors include a `fix` field in plain language and a different `next_actions` list biased toward recovery. This is Fielding's HATEOAS constraint from REST, applied to CLIs — but with forms (typed inputs), not just links.

### Principle 3: Self-documenting command tree
Root command (no args) returns the full command tree as JSON — one call, agent knows everything. No `--help` parsing, no man pages.

### Principle 4: Protect context
Agents have finite context windows. A CLI dumping 10,000 log lines consumes half the agent's working memory. Rules:
- **Truncate by default** — last 30 lines, not all of them.
- **Point to the full output** — include a file path when truncated.
- **Auto-limit lists** — reasonable cap, `--count` to adjust.

### Principle 5: NDJSON for the temporal dimension
For long-running commands, stream NDJSON (one JSON object per line) with a `type` discriminator. **The last line is always the standard HATEOAS envelope**, so tools that don't understand streaming just read the last line.

Event types: `start`, `step`, `progress`, `log`, `event`, `result` (terminal success), `error` (terminal failure). The agent sees each step as it happens, reacts mid-stream, cancels/retries without waiting.

### Response envelope schemas

**Success:**
```
{ ok: true, command: string, result: object, next_actions: NextAction[] }
```

**Error:**
```
{ ok: false, command: string, error: { message, code }, fix: string, next_actions: NextAction[] }
```

**Stream event:**
```
{ type: "start" | "step" | "progress" | "log" | "event" | "result" | "error", ... }
```

---

## Implementation stacks

| Language | Framework | Used by |
|----------|-----------|---------|
| Python | **Typer** (Click with type hints) | default for new organism work |
| Go | **Cobra + Viper** | kubectl, gh, hugo |
| Rust | **clap** (derive API) | ripgrep, uv, ruff |
| Node | **oclif** (Jeff Dickey's, built on the 12-factor principles above) | Heroku CLI, Salesforce CLI |

All give `--help`, subcommands, shell completion, and conventional flag parsing for free. Don't hand-roll argv parsing — every hand-rolled parser eventually fails on `--flag=value` vs `--flag value` or `--`-terminated argv.

## Patterns worth stealing

- **`tool doctor`** — self-diagnosis subcommand. Exits non-zero if any check fails. Used by brew, rustup, flutter, op. Cheap to add, high value.
- **`tool completion <shell>`** — emits shell completion script.
- **`tool schema`** (agent-facing) — emits JSON describing commands, flags, exit codes. Agent self-discovery without parsing `--help`.
- **`--dry-run`** — shows what would happen without doing it. Especially for destructive commands.
- **`--output=json|yaml|table`** — uniform output format selector across subcommands (kubectl, gh, aws pattern).
- **Verb symmetry** — if you have `create`, you need `delete`; `get` pairs with `list`; `start` with `stop`. Missing verbs are a code smell.
- **Exit with usage on bare `tool`** — print help and exit non-zero. Don't drop into a REPL, don't wait.
- **Flag aliases only for the top ~5 most-used flags.** Every extra short flag is a conflict waiting to happen.
- **`--` pass-through terminator** — for CLIs that forward args to another process.

## Anti-patterns

- **Interactive-only paths.** Every prompt needs a flag override.
- **Silent success that should have been feedback.** "Did it work?" is a design failure.
- **Flags that change semantics based on other flags' values.** Mode switches should be subcommands, not flag combos.
- **Hand-rolled argv parsing.** Use a framework.
- **Unstable error messages.** Breaks agent workflows and log alerts.
- **Config discovered by walking parent directories with no `--config` override.** Document the search order and allow explicit override.
- **`sudo` in the tool itself.** Let the user escalate. Never invoke `sudo` internally.
- **Table borders** (un-greppable, un-parseable — Dickey factor 8, Heroku style guide).
- **`*:list` / `*:ls` commands when the bare topic already lists** (Heroku convention).
- **Phoning home without consent** (clig.dev Analytics).
- **Output format changes without versioning.** Once the CLI has users, output is a contract.

## See also

- `container-design` skill — choosing tool / skill / agent as a capability wrapper
- `organogenesis` skill — designing the skill layer that wraps a CLI
- `~/epigenome/marks/finding_vivesca_mcp_context_cost.md` — measurement of actual MCP surface cost before migrating
- `~/docs/solutions/grammers-mtproto-agent-auth.md` — worked example: Telegram auth as a two-step agent CLI (DC migration, raw TL calls, SRP 2FA)
