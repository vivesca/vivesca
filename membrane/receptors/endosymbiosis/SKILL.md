---
name: endosymbiosis
description: Integrate an external tool as a first-class organelle. "absorb"
triggers:
  - absorb
  - endosymbiosis
  - integrate
  - organelle
  - wrap
  - ingest
user_invocable: true
model: sonnet
context: fork
---

# Endosymbiosis — Absorbing External Organisms into the Cell

The mitochondrion was once a free-living bacterium. The chloroplast too. Endosymbiosis: a foreign organism is absorbed, loses its autonomy, and becomes an organelle — permanently integrated, mutualistic, no longer separable.

This is the endocytosis pattern generalized. Endocytosis absorbed 161 RSS feeds. The organism didn't link to them — it ingested them.

## When to Use

- An external tool is called repeatedly via subprocess or API
- A package is depended on but not understood by the organism
- You want a service to become an organelle, not a dependency
- An integration is load-bearing and needs organism-level reliability

## Absorption Protocol

### Step 1 — Pre-absorption audit

**Use droid explore for recon** — don't burn CC tokens reading the external codebase:
```bash
ribosome -m "custom:glm-4.7" --cwd <external-repo> \
  "Read the source files and summarize: (1) what it does and key functions, \
  (2) external dependencies, (3) path assumptions, (4) how the organism \
  currently wraps it. Output a concise summary for spec writing."
```

From the droid summary, answer four questions:
1. What does the external organism produce? (output type)
2. How does the organism currently invoke it? (command, API, file)
3. What would break if it disappeared? (blast radius)
4. Does it have state the organism doesn't own? (risk)

If blast radius is high and state is foreign: absorb. If blast radius is low: consider endocytosis (one-shot ingestion) instead.

### Step 2 — Wrap the membrane

Create a thin adapter that hides the external surface:
```python
# Before: organism calls external directly
result = subprocess.run(["external-tool", "--flag", input])

# After: organism calls an organelle
result = organelle.process(input)  # organelle owns the external call
```

The organism should not know what the organelle runs internally.

### Step 3 — Feed it organism nutrients

Make the organelle read from organism sources:
- Config from organism's config system (not its own dotfiles)
- Auth from organism's keychain (not its own credentials)
- Logs via organism's telemetry (not its own log files)

### Step 4 — Lysosomal digestion

After absorption, the lysosome breaks down foreign material and keeps only what the organism needs. A blind port is undigested — foreign DNA running inside the cell.

For each absorbed module, audit:

1. **Should it exist?** Does the organism already have this capability in another organelle? Could it be 10 lines instead of 500?
2. **Dead code?** Functions, branches, or features that served the foreign organism but not this one. Hardcoded dates, completed-purpose logic, unused flags.
3. **Foreign patterns?** Idioms from the source language that don't belong in Python. Manual error propagation, explicit enum matching, double-encoded serialization, structs-as-classes.
4. **Hardcoded paths?** The foreign organism had its own filesystem conventions. Replace with `metabolon.locus` or organism config.
5. **Wrong abstraction level?** The foreign organism may have been a CLI with arg parsing, table formatting, color output. The organelle may only need the core logic — the CLI is a thin `_cli()` wrapper, not the organelle's identity.
6. **Fragile external dependencies?** Scraped URLs, API endpoints, auth patterns that may have changed since the foreign code was written.

The test: could a new contributor read this organelle and understand it in 60 seconds? If not, it's undigested.

### Step 5 — Verify mutualism

The absorbed organelle must give more than it costs:
| Metric | Before absorption | After absorption |
|--------|------------------|-----------------|
| Invocation overhead | | |
| Error handling | | |
| Organism visibility into behavior | | |
| Upgrade surface (risk) | | |

### Step 6 — Remove the external surface

Once the organelle is stable: remove all direct invocations of the original external tool from organism code. The original binary/package may remain installed — but only the organelle may call it.

## Anti-patterns

- **Symbiosis without absorption:** wrapping but keeping direct calls elsewhere. Partial endosymbiosis is unstable.
- **Absorbing junk DNA:** not every external tool deserves organelle status. If it's called once, use endocytosis.
- **Over-abstracting the membrane:** the wrapper should be thin. A fat adapter is a parasite, not an organelle.
