# Tool Replacement Checklist

When a new CLI tool replaces an old one, complete all items before considering the migration done.

## Checklist

1. **Migrate data.** Run migration or verify the new tool has all historical data from the old store.
2. **Rewire LaunchAgents/cron.** Update any scheduled jobs to point at the new binary. Reload with `launchctl unload/load`.
3. **Update tool-index.** Add the new tool to `~/officina/claude/tool-index.md` so Claude can discover it.
4. **Update MEMORY.md** if the old tool was referenced there.
5. **Decommission old artefacts.** Archive or remove: old DB, old sync scripts, old binary. Don't leave parallel data stores.
6. **Smoke test.** Run the new tool end-to-end: sync, query, display. Verify LaunchAgent fires correctly (`launchctl list | grep <label>`).

## Origin

Sopor replaced oura-cli + somnus + nyx (Mar 2026). LaunchAgent and tool-index were missed, leaving dual data stores and an undiscoverable CLI for 5 days.
