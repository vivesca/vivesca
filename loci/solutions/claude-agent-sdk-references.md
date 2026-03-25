# Claude Agent SDK — Real-World References

## HappyClaw (riba2534/happyclaw)

Best real-world Claude Agent SDK usage example found so far (evaluated 2026-02-24).

**Key files:**
- `container/agent-runner/src/index.ts` — SDK `query()` call with streaming, session resume, memory flush, pre-compact hooks
- `container/agent-runner/src/ipc-mcp-stdio.ts` — MCP server over filesystem IPC (no network needed)
- `src/container-runner.ts` — Docker lifecycle, volume mounts, output parsing
- `src/mount-security.ts` — production-grade path allowlist/blocklist

**Patterns worth stealing:**
1. **Pre-compact transcript archiving** — `createPreCompactHook` archives full transcript to markdown before compaction
2. **Memory flush as constrained turn** — after compact, runs agent turn limited to memory tools only (disallows Bash/WebSearch/etc via `disallowedTools`)
3. **`MessageStream` async iterable** — push-based message stream for feeding follow-up messages to running SDK session
4. **MCP-over-filesystem IPC** — agent writes JSON to mounted dir, host polls. Cross-process communication without sockets.
5. **Dangerous env var blocklist** — comprehensive set: LD_PRELOAD, NODE_OPTIONS, PATH, BASH_ENV, SSH_AUTH_SOCK, etc.

**Full evaluation:** `~/epigenome/chromatin/Decisions/2026-02-24-happyclaw-evaluation.md`
