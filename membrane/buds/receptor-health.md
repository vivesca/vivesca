---
name: receptor-health
description: Nightly receptor integrity + dormancy audit. Probes attachments, classifies activation state, logs anoikis candidates.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Run the receptor health check for the vivesca organism.

1. Call `integrin_probe` via the MCP server or directly via Python:
   ```bash
   cd ~/code/vivesca && uv run python -c "from metabolon.tools.integrin import integrin_probe; print(integrin_probe())"
   ```

2. Call `integrin_apoptosis_check`:
   ```bash
   cd ~/code/vivesca && uv run python -c "from metabolon.tools.integrin import integrin_apoptosis_check; print(integrin_apoptosis_check())"
   ```

3. Report:
   - Total receptors, attached vs detached
   - Activation state distribution (open / extended / bent)
   - Anoikis candidates (bent + all ligands detached) -- these need retirement or repair
   - Focal adhesions (shared dependencies) -- single points of failure
   - Mechanically silent binaries -- exist but don't respond

4. If anoikis candidates found, check ~/notes/receptor-retirement.md for the log.

5. For each anoikis candidate, check if the missing binary is:
   - Renamed (grep for the binary name in ~/code/vivesca/effectors/)
   - Removed intentionally (check git log)
   - Actually broken (needs fix)

Present a clear action list: fix, retire, or investigate.
