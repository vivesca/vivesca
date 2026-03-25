---
name: endosymbiosis
description: Absorb an external tool or package into the organism with full integration. "endosymbiosis", "integrate tool", "absorb package", "adopt external", "lustro pattern".
user_invocable: true
model: sonnet
context: fork
---

# Endosymbiosis — Absorbing External Organisms into the Cell

The mitochondrion was once a free-living bacterium. The chloroplast too. Endosymbiosis: a foreign organism is absorbed, loses its autonomy, and becomes an organelle — permanently integrated, mutualistic, no longer separable.

This is the lustro pattern generalized. Lustro absorbed 161 RSS feeds. The organism didn't link to them — it ingested them.

## When to Use

- An external tool is called repeatedly via subprocess or API
- A package is depended on but not understood by the organism
- You want a service to become an organelle, not a dependency
- An integration is load-bearing and needs organism-level reliability

## Absorption Protocol

### Step 1 — Pre-absorption audit

Answer four questions:
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

### Step 4 — Verify mutualism

The absorbed organelle must give more than it costs:
| Metric | Before absorption | After absorption |
|--------|------------------|-----------------|
| Invocation overhead | | |
| Error handling | | |
| Organism visibility into behavior | | |
| Upgrade surface (risk) | | |

### Step 5 — Remove the external surface

Once the organelle is stable: remove all direct invocations of the original external tool from organism code. The original binary/package may remain installed — but only the organelle may call it.

## Anti-patterns

- **Symbiosis without absorption:** wrapping but keeping direct calls elsewhere. Partial endosymbiosis is unstable.
- **Absorbing junk DNA:** not every external tool deserves organelle status. If it's called once, use endocytosis.
- **Over-abstracting the membrane:** the wrapper should be thin. A fat adapter is a parasite, not an organelle.
