---
name: agent-cli
description: Design patterns for CLIs intended to be used by AI agents rather than humans. Consult when building a new CLI that Claude will invoke, or when debugging why an existing CLI doesn't work well in agent sessions.
user_invocable: false
---

# agent-cli

Reference patterns for building CLIs that agents drive, not humans. The design constraints differ significantly from human-facing CLIs.

Full worked example: `graphis` — Telegram bot manager built specifically for agent use.

## Core difference

| Human CLI | Agent CLI |
|-----------|-----------|
| Interactive prompts OK | Every step must be non-blocking |
| One command does everything | Split at every human-in-the-loop point |
| State lives in the process | State must persist to disk between invocations |
| Errors can be vague | Errors must be actionable (agent needs to know what to do next) |
| `/dev/tty` reads are fine | `/dev/tty` reads hang the agent session |

## Pattern 0: Eliminate human-in-the-loop before designing around it

Before splitting a step into two commands, ask: **can the human step be removed entirely?**

| Human step | Elimination options |
|------------|-------------------|
| SMS/OTP code | App-level session reuse (Telegram session persists indefinitely — auth is one-time) |
| 2FA password | Store in keychain; read with `security find-generic-password` |
| CAPTCHA | Headless-detectable endpoint → use API instead of web scrape |
| OAuth browser flow | Service account / API key / long-lived token |
| Manual approval | Webhook + auto-confirm if criteria met |
| Copy-paste output | Pipe directly to next command; save to keychain or file |

**The goal is zero recurring human steps.** One-time setup (initial auth, keychain seeding) is acceptable. Anything that recurs per-operation is a design flaw.

**graphis example:** The SMS code is genuinely one-time — session persists to `session.bin` and survives reboots. The design is correct: auth once, never again. If you're being asked for a code repeatedly, the session is being deleted or not saved correctly — fix that, don't add a recurring human step.

**Red flags that mean you haven't eliminated enough:**
- User must copy a value from one tool and paste it into another → pipe it or save to keychain
- User must approve each operation → add a `--yes` flag and document when it's safe to use
- User must watch for output and react → write result to a file the next step reads

## Pattern 1: Split at every remaining human-in-the-loop point

Once you've eliminated what you can, any *genuinely unavoidable* human step (first-time SMS code, physical security key) must be a separate command invocation.

**Structure:**
```
cmd step1 <args>     → triggers external action, saves state, prints next instruction
cmd step2 <secret>   → reads saved state, completes with human-provided secret
```

**State to persist between steps** (always more than you think):
- All parameters needed to reconstruct the request (phone number, hash, nonce)
- Which server/DC/endpoint to reconnect to — connection state is NOT preserved
- Any session or auth key established in step 1

**graphis example:**
```bash
graphis auth +phone        # → saves {phone, phone_code_hash, dc} to pending-auth.json
graphis auth-complete CODE # → reads pending-auth.json, signs in on correct DC
```

## Pattern 2: Persist connection state explicitly

Libraries assume you'll reconnect to the same server. They're wrong — the agent will start a fresh process for step 2. Anything that determines *where* to connect must be saved explicitly.

Common failure: step 1 migrates to a different server (DC migration, regional redirect, load balancer), step 2 connects to the default and gets a transport error.

**Checklist before saving state:**
- [ ] Which host/DC/region did step 1 actually connect to?
- [ ] Is that encoded in the session file, or do I need to save it separately?
- [ ] Will the library honour it on reconnect without explicit configuration?

**graphis example:** grammers session encodes auth keys per DC but grammers ignores the DC on reconnect — always uses default. Had to save DC to `dc.txt` and pass via `InitParams::server_addr`.

## Pattern 3: Use raw protocol calls when the high-level API hides needed state

High-level library methods often wrap responses in opaque types with private fields. If you need data from the response (e.g. a hash, a nonce, a token) to persist across invocations, the high-level API may block you.

**Options in order of preference:**
1. **Raw protocol call** — call the underlying RPC directly, get the struct with public fields
2. **Check if the type implements `Debug`/`serde`** — if so, serialise or parse the debug repr
3. **Fork the library** — add a public accessor (last resort, maintenance burden)

Do NOT use `unsafe` transmute to access private fields — layout assumptions break across compiler versions.

**graphis example:** `LoginToken.phone_code_hash` is `pub(crate)`. Used raw TL `auth.SendCode` instead, which returns `auth.SentCode` with public `phone_code_hash` field.

## Pattern 4: Handle library-transparent errors manually

Libraries written for human apps often silently handle protocol-level redirects (DC migration, server errors, retries). When you bypass the high-level API, you take on that responsibility.

**Common Telegram MTProto errors agents hit:**
- `PHONE_MIGRATE(N)` — phone is registered on DC N; reconnect to that DC and retry
- `FILE_MIGRATE(N)` — file is on DC N
- `NETWORK_MIGRATE(N)` — network-level redirect

**Pattern for handling:**
```rust
match client.invoke(&request).await {
    Ok(r) => r,
    Err(e) if e.to_string().contains("PHONE_MIGRATE") => {
        let dc = parse_dc_from_error(&e.to_string());
        save_dc(dc);                        // persist for future invocations
        client = connect_to_dc(dc).await?;  // reconnect
        client.invoke(&request).await?      // retry
    }
    Err(e) => return Err(e.into()),
}
```

## Pattern 5: Error messages must tell the agent what to do next

Human CLI errors say what went wrong. Agent CLI errors say what to run next.

```
# Human-facing
Error: Not authenticated

# Agent-facing
Error: Not authenticated. Run: graphis auth +<your_phone>
```

The agent reads the error and acts on it — it needs a concrete next command, not a diagnosis.

## Pattern 6: Idempotent steps where possible

The agent may retry a step if it's unsure whether it succeeded (background task, network hiccup). Steps should be safe to re-run.

- `auth`: if already signed in, print "Already signed in." and exit 0
- `start-bot`: sending `/start` twice is harmless
- `create`: check if bot exists before creating (BotFather will error clearly if not)

## Worked example: graphis auth design

```
Problem: Telegram auth requires an SMS code the agent cannot receive.

Naive design (fails):
  graphis auth +phone   ← blocks waiting for stdin that never comes

Two-step design (works):
  graphis auth +phone           ← agent runs; Telegram sends SMS to user
  # user tells agent the code
  graphis auth-complete CODE    ← agent runs with code

State persisted to pending-auth.json:
  { phone, phone_code_hash, dc }

DC migration handled:
  - Default DC connection → PHONE_MIGRATE(5) error
  - Reconnect to 91.108.56.130:443 (DC5)
  - Save "5" to dc.txt
  - All future make_client() calls use dc.txt to set server_addr
```

## Checklist before shipping an agent-facing CLI

- [ ] **Every human step audited** — is it truly unavoidable, or can it be eliminated via keychain, session persistence, API key, or `--yes` flag?
- [ ] No blocking stdin reads (`io::stdin().read_line()`, `/dev/tty`)
- [ ] Every human-in-the-loop step is a separate subcommand
- [ ] State between steps is fully serialised to disk (not just session file)
- [ ] Connection target (host, DC, region) persisted explicitly if it can change
- [ ] All errors include a suggested next command
- [ ] Steps are idempotent or explicitly documented as non-idempotent
- [ ] `--help` output is accurate (agent may read it to self-discover commands)

## See also

- `graphis` skill — full worked example
- `~/docs/solutions/grammers-mtproto-agent-auth.md` — concrete implementation: DC migration code, raw TL auth.SendCode, LoginToken workaround, SRP 2FA, Cargo.toml deps, recovery procedure
