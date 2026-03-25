# Healthcheck vs Experience Test

**Pattern:** Declaring a system "ready" after a connectivity check, then discovering broken UX when a human actually uses it.

**Example:** Lucerna DR server — `claude --print "HELLO"` worked, but actual usage revealed: missing .zshrc (zsh wizard), no hooks, no memory files, no docs symlink, missing CLI tools (eza/bat/fd), Linux-incompatible binaries (fasti/moneo), Tailscale crash-loop from stale state.

**Rule:** After building any environment meant for human use, test it *as* the user:
1. SSH in interactively (not via `fly ssh console -C "echo OK"`)
2. Run the actual workflow (not a smoke test)
3. Check the periphery (aliases, prompt, tools, hooks) — not just the core function
4. Every gap found by the user instead of by you is a miss

**Why it matters:** A healthcheck tests "is it alive?" An experience test asks "can someone work here?" These are different questions with different answers.
