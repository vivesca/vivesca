---
name: MCP Ecosystem Patterns 2026
description: MCP server ecosystem research — popular servers, tool design patterns, composition, security, performance, Claude Code integration. March 2025–March 2026.
type: reference
---

## Key Facts

- Ecosystem: 7,300+ servers on Smithery, 3,000+ on MCP.so. Majority are demos; ~20% production-quality.
- Top by usage (Smithery): Sequential Thinking (5,550+), wcgw (4,920+), GitHub, Brave Search.

## Transport Decision Rule
- stdio → local, single client, desktop (sub-ms, 10K ops/sec)
- Streamable HTTP → remote, cloud, multi-client (OAuth 2.1 required, scales horizontally)
- SSE → deprecated March 2025; backward compat only

## Protocol Versions
- 2025-03-26: Streamable HTTP, pagination
- 2025-06-18: OAuth 2.1 finalized, ResourceLink, output schemas
- 2025-11-25: Tasks (async), URL elicitation, Sampling with tools, CIMD (replaces dynamic client registration)

## Tool Design: 4 Patterns (Klavis)
1. Semantic search (vector index, load on match)
2. Workflow bundling (composite tools, internal multi-step)
3. Code mode (single execute_code tool, sandboxed)
4. Progressive discovery (list → detail → execute)

## Claude Code ToolSearch (v2.1.7+)
- Fires when tools >10% of context window
- Before: 71K tokens startup → After: 5K tokens (95% reduction)
- `serverInstructions` field = what ToolSearch matches on; most important field to write
- Bug (open): permission prompts coupled to lazy-load step; pre-authorized tools still prompt

## Security Attack Taxonomy
- Prompt injection via tool output (GitHub issue attack, May 2025)
- Tool poisoning (malicious descriptions in registry)
- CVE-2025-6514: mcp-remote RCE via OAuth authorization_endpoint (437K downloads affected)
- Filesystem sandbox escape: symlink traversal in official Anthropic server
- Credential theft: env vars accessible to co-process; args visible in context window

## Credential Management Gold Standard
- Fetch from OS keychain AT execution time, never pass as args
- Never in model context window; never in logs without redaction

## OAuth Requirements (2025-06-18 spec)
- PKCE S256 mandatory for all clients
- Resource Indicators (RFC 8707): token audience bound to specific server
- Short-lived tokens (minutes-hours)
- November 2025: Dynamic Client Registration → Client ID Metadata Documents (CIMD)

## Performance: 3 Bottlenecks
1. Connection overhead (80%): fix with connection pool → 200ms → 5ms
2. Cache misses: 60s validity + background refresh → 100ms → 1ms
3. Sequential processing: batch similar requests

## Tool Count Economics
- Simple tool: 50–100 tokens; Enterprise tool: 500–1,000 tokens
- 7 servers = 67,300 tokens reported = 33.7% of 200K context
- Cursor hard limit: 40 MCP tools total

## Composition Patterns
1. FastMCP mount() with namespace prefix (v3.0.0+)
2. Gateway (reverse proxy: auth, routing, audit, policy)
3. Aggregator server (Pipedream 2,500 APIs, AnyQuery SQL over 40 apps)
4. NCP orchestrator (MCP server that calls other MCP servers) — emerging

## Framework Comparison
- FastMCP Python: best DX for Python, mount/proxy composition, official-adjacent
- FastMCP TypeScript (punkpeye): edge deployment on Cloudflare Workers
- Official TS SDK: low-level, spec compliance, minimal opinions
- Speakeasy/Stainless: generate from OpenAPI spec; Cloudflare Workers deploy

## Novel Servers Worth Adopting
- Pipedream: 2,500 APIs via one server
- AnyQuery: SQL over Notion/GitHub/Spotify/Airtable
- Financial Datasets / EODHD: market data, SEC filings
- PersonalizationMCP: 90+ tools, 6 platforms, OAuth2

## Source Quality Notes
- gofastmcp.com WebFetch works
- modelcontextprotocol.io WebFetch works
- blog.modelcontextprotocol.io works
- workos.com blog works
- blog.gitguardian.com works
- claudefa.st works
- thenewstack.io returns 403
