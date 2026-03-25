# MCP vs Skills vs CLI for AI Agents: Enterprise Architecture

> Created: 2026-02-14
> Context: Consulting reference for Capco AI Solution Lead conversations

## The One-Sentence Answer

**MCP = tool access governance. Skills = knowledge governance. CLI = the execution layer under both.**

They're complementary, not competing. An enterprise needs all three.

## Where CLI is Sufficient (or Better)

| Factor | Why CLI wins |
|--------|-------------|
| **Single orchestrator** | One Claude Code / Codex instance — no sharing needed |
| **Existing tooling** | `gh`, `kubectl`, `aws`, `docker` are battle-tested, vendor-maintained |
| **Composability** | Unix piping beats structured protocols for ad-hoc chaining |
| **Token cost** | No schema overhead per turn (~350-5,600 tokens/turn saved) |
| **Maintenance** | CLI tools updated by vendors; MCP servers are yours to maintain |
| **Self-documenting** | `--help` and man pages; agents can discover capabilities natively |

## Where Enterprises Still Need MCP

### 1. Multi-Agent / Multi-User Access Control
- CLI runs as whoever's logged in — no user-level granularity
- MCP gateways provide per-user OAuth, RBAC, attribute-based access
- **Trigger:** 10+ agents or users hitting the same backend services

### 2. Audit Trails & Compliance
- EU AI Act classifies autonomous multi-step agents as "High-Risk" — requires immutable action logs
- SOC 2 Type II, HIPAA, PCI all need centralized audit trails
- CLI audit = parsing shell history (fragile, not immutable)
- MCP gateways log every tool invocation centrally with timestamps, user context, parameters
- **Trigger:** regulated industry (banking, healthcare, government)

### 3. Centralised Credential Management
- CLI stores creds locally (`~/.aws/credentials`, `~/.kube/config`)
- MCP centralises credential vaulting with rotation — no secrets on dev machines
- **Trigger:** security team won't allow local credential storage

### 4. Stateful / Streaming Interactions
- Database cursors, real-time feeds, websocket sessions
- CLI is request-response; MCP maintains long-lived connections
- **Trigger:** agent needs to hold open a connection (not just fire-and-forget)

### 5. Model-Agnostic Tool Sharing
- One MCP server works with Claude, GPT, Gemini, local models
- CLI works when you have ONE orchestrator — enterprise has many
- **Trigger:** multiple LLM vendors/platforms consuming the same tools

### 6. Centralised Policy Enforcement
- Rate limiting, content filtering, PII redaction **before** the tool executes
- CLI has no interception layer — the command runs or it doesn't
- MCP gateways act as policy enforcement points
- **Trigger:** need to enforce guardrails across diverse agent deployments

### 7. Non-Technical User Access
- CLI requires shell access and knowledge
- MCP can be exposed through chat UIs, Copilot plugins, web interfaces
- **Trigger:** business users (not developers) operating AI agents

### 8. Dynamic Tool Discovery
- MCP's typed schemas let agents understand capabilities programmatically
- CLI `--help` works but is unstructured text requiring parsing
- **Trigger:** agents that need to discover and compose tools they haven't seen before

## The Decision Framework

```
Is there ONE operator with shell access?
  → CLI + skills. You're done.

Multiple agents/users hitting shared tools?
  → Do you need audit trails or compliance?
    → Yes: MCP gateway (MintMCP, Composio, etc.)
    → No but need model-agnostic sharing: MCP server (lightweight)
    → No and single model: CLI is still fine
```

## E2B / Sandboxes: MCP Gets Stronger, Not Weaker

E2B (Firecracker microVM sandboxes, 150ms boot) is now de facto standard for agent code execution — 88% of Fortune 100, $21M Series A. Every agent gets an isolated VM with full shell access.

**Naive take:** if every agent has CLI in a sandbox, MCP is redundant.

**Actual pattern:** E2B embeds MCP as the control plane. Every E2B sandbox ships with Docker's MCP Catalog (200+ curated tools). E2B itself has an MCP server. The architecture:

```
E2B sandbox (execution security — isolates untrusted code)
  └── MCP gateway (access governance — controls what the sandbox can reach)
       └── Docker MCP Catalog (200+ audited tool implementations)
```

**Why sandboxes increase MCP's value:**
- Thousands of ephemeral sandboxes = thousands of potential credential leaks without centralised management
- Each sandbox needs scoped access (this agent can read Jira, not write; can query DB, not drop tables)
- Audit trail across ephemeral sandboxes is impossible without a central control plane
- Sandboxes die — their shell history dies with them. MCP gateway logs persist.

**For single operators:** E2B + CLI makes MCP fully redundant. You don't need governance over yourself.

**For a bank with 200 agents in sandboxes:** MCP becomes the immune system. Without it, you have 200 unmonitored shells with production credentials.

## Skills: The Missing Layer — Enterprise Knowledge Governance

MCP connects agents to tools. But no MCP server tells the agent *how* to use those tools in your organisation's context. That's what skills do.

### What Skills Capture That MCP Can't

| Layer | What it governs | Example |
|-------|----------------|---------|
| **MCP** | Tool access — who can call what, with which creds | "Agent can query prod DB read-only" |
| **Skills** | Institutional knowledge — how we use tools here | "Always check feature flag cache (5min TTL) before deploying" |
| **CLI** | Execution — the actual commands | `kubectl rollout restart deployment/api` |

### Enterprise Value of Skills

1. **Codified workflows** — "How we do a release" becomes executable steps, not a Confluence page nobody reads
2. **Onboarding acceleration** — New engineer or new AI agent inherits team conventions immediately
3. **Gotcha capture** — "This API returns 200 on failure" lives in the skill context, not in one person's head
4. **Version-controlled knowledge** — Git repo, reviewable PRs, audit trail on knowledge changes (unlike tribal knowledge)
5. **Context injection** — Skills inject domain constraints the LLM couldn't know otherwise (regulatory rules, internal naming conventions, deployment quirks)
6. **Reference skills** — Non-user-facing skills that guide agent routing decisions (e.g., "which tool to use for web search" or "how to handle browser automation")

### The Enterprise Architecture

```
Skills (knowledge governance)
  ├── Workflow skills: "how we deploy", "how we review PRs"
  ├── Domain skills: "our compliance rules", "our API conventions"
  ├── Reference skills: routing logic, tool selection, fallback chains
  └── Gotcha skills: "known issues with service X"

MCP Gateway (tool access governance)
  ├── Credentials: centralised, rotated, scoped
  ├── Audit: every tool invocation logged
  ├── RBAC: per-user/per-agent permissions
  └── Policy: rate limits, PII redaction

CLI (execution layer)
  └── The actual commands both layers ultimately invoke
```

### Why This Matters for Consulting

Most enterprise AI agent discussions focus only on MCP (tool access). Skills are the knowledge management layer that determines whether agents make *good* decisions, not just *permitted* ones. A bank can give an agent MCP access to Jira — but without a skill saying "always tag compliance tickets with the regulatory-ref field", the agent will create tickets that pass RBAC but fail process.

**Pitch framing:** "MCP is your agent's keycard. Skills are your agent's training manual."

## Enterprise MCP Gateway Landscape (Feb 2026)

Key players: MintMCP (SOC 2 Type II, one-click deploy), Composio, Strata (identity fabric), Airia, Itential (infra-specific). All provide OAuth, audit logging, RBAC, rate limiting.

## Sources

- [OneUptime: CLI is the New MCP](https://oneuptime.com/blog/post/2026-02-03-cli-is-the-new-mcp/view)
- [CData: 2026 Enterprise MCP Adoption](https://www.cdata.com/blog/2026-year-enterprise-ready-mcp-adoption)
- [MintMCP: Enterprise AI Infrastructure](https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp)
- [Strata: Securing MCP Servers](https://www.strata.io/agentic-identity-sandbox/securing-mcp-servers-at-scale-how-to-govern-ai-agents-with-an-enterprise-identity-fabric/)
- [Integrate.io: MCP Gateways and Security Tools](https://www.integrate.io/blog/best-mcp-gateways-and-ai-agent-security-tools/)
- [Tinybird: MCP vs APIs](https://www.tinybird.co/blog/mcp-vs-apis-when-to-use-which-for-ai-agent-development)
- [E2B: Enterprise AI Agent Cloud](https://e2b.dev/)
- [Docker + E2B: Building Trusted AI](https://www.docker.com/blog/docker-e2b-building-the-future-of-trusted-ai/)
- [E2B Series A — $21M](https://e2b.dev/blog/series-a)
