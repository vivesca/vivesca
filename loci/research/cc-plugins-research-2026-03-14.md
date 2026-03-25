# Claude Code Plugin Ecosystem Research
_March 2026 — researched by researcher agent_

---

## 1. Where Plugins Live

### Official registries
- **`anthropics/claude-plugins-official`** (GitHub, 10.7K stars) — Anthropic-curated. 30 plugins in `/plugins/`, plus `/external_plugins/` for third-party. Install via `/plugin install <name>@claude-plugin-directory` or browse `/plugin > Discover`. [GitHub](https://github.com/anthropics/claude-plugins-official)
- **`anthropics/claude-code` `/plugins/`** — built-ins shipped with CC itself (e.g. `/batch`, `/simplify`). Not separately installable. [GitHub](https://github.com/anthropics/claude-code/tree/main/plugins)
- **Claude.com plugin pages** — e.g. `claude.com/plugins/typescript-lsp` — official install pages.

### Community registries
- **`Chat2AnyLLM/awesome-claude-plugins`** — 834 plugins across 43 marketplaces, updated Jan 2026. [GitHub](https://github.com/Chat2AnyLLM/awesome-claude-plugins)
- **`hesreallyhim/awesome-claude-code`** — curated: skills, hooks, slash-commands, agents, orchestrators. Well-maintained. [GitHub](https://github.com/hesreallyhim/awesome-claude-code)
- **`VoltAgent/awesome-claude-code-subagents`** — 100+ standalone subagents across 16 categories. [GitHub](https://github.com/VoltAgent/awesome-claude-code-subagents)
- **`0xfurai/claude-code-subagents`** — 100+ production-ready subagents including framework experts. [GitHub](https://github.com/0xfurai/claude-code-subagents)
- **claude-plugins.dev** — community registry with CLI install tool; indexes public plugins + skills. 1399 skills across 343 plugins. [Site](https://claude-plugins.dev/)
- **claudemarketplaces.com** — aggregator. [Site](https://claudemarketplaces.com/)

---

## 2. Official Anthropic Plugins (claude-plugins-official) — Full Inventory

30 plugins. Currently installed from this repo: superpowers. Gaps to evaluate:

| Plugin | What It Does | Gap vs Installed? |
|--------|-------------|-------------------|
| `agent-sdk-dev` | Scaffolds Claude Agent SDK apps (Python/TS). `/new-sdk-app` command + verifier agents | **New** — SDK development workflow |
| `clangd-lsp` | C/C++/ObjC LSP integration | N/A for Terry's stack |
| `claude-code-setup` | Project onboarding automation | Likely redundant with CLAUDE.md workflow |
| `claude-md-management` | Audits CLAUDE.md quality; `/revise-claude-md` captures session learnings | **Potentially useful** — see below |
| `code-review` | 4 parallel agents: CLAUDE.md compliance, bugs, context issues. Confidence-scored | Partial overlap with compound-engineering CE review agents. Anthropic-official version. |
| `code-simplifier` | Dedicated simplification agent (same as CE's `code-simplicity` reviewer) | Already covered by compound-engineering |
| `commit-commands` | `/commit`, `/commit-push-pr`, `/clean_gone` — smart commits + PR creation | **Potentially useful** — `/commit-push-pr` is a nice atomic command |
| `csharp-lsp` | C# LSP | N/A |
| `example-plugin` | Reference implementation | Dev use only |
| `explanatory-output-style` | Makes Claude explain reasoning | Style pref, not workflow |
| `feature-dev` | 7-phase feature workflow (discovery → architecture → implementation → review). 3 agents: `code-explorer`, `code-architect`, `code-reviewer`. 89K installs. | Overlaps with strategos + compound-engineering. Simpler/more guided. |
| `frontend-design` | Production-grade UI design workflow; taste-aware generation | **Useful if doing frontend work** |
| `gopls-lsp` | Go LSP | Useful if Go work picks up |
| `hookify` | Create CC hooks via markdown config. `/hookify`, `/hookify:list`, `/hookify:configure` | **High value** — see below |
| `jdtls-lsp` | Java LSP | N/A |
| `kotlin-lsp` | Kotlin LSP | N/A |
| `learning-output-style` | Teaching-mode output style | N/A |
| `lua-lsp` | Lua LSP | N/A |
| `php-lsp` | PHP LSP | N/A |
| `playground` | Experimentation sandbox | Dev use only |
| `plugin-dev` | Plugin development tooling | Dev use only |
| `pr-review-toolkit` | 6 agents: comment accuracy, test coverage, silent failures, type design, code review, simplification | **Worth evaluating** — `silent-failure-hunter` and `pr-test-analyzer` are not in compound-engineering |
| `pyright-lsp` | Python LSP (Pyright) | **Useful** — Python is active |
| `ralph-loop` | Iterative loop: Claude works → exits → hook intercepts → re-runs same prompt. `/ralph-loop`, `/cancel-ralph`. | **Caveat: quota killer** — see below |
| `ruby-lsp` | Ruby LSP | N/A |
| `rust-analyzer-lsp` | Rust LSP with go-to-definition, find-references, real-time diagnostics | **High value** — Rust is primary language |
| `security-guidance` | Hook-based security guardrails (not static analysis — behavioral enforcement at write-time) | Complementary to static-analysis |
| `skill-creator` | Create/improve/eval/benchmark skills. Runs evals on skills. | **High value** — see below |
| `swift-lsp` | Swift LSP | N/A |
| `typescript-lsp` | TS/JS LSP with real type checking, go-to-definition, cross-project error detection | **High value** if TS work increases |

---

## 3. The Every Marketplace (EveryInc)

**EveryInc publishes exactly one plugin: `compound-engineering-plugin`.** Already installed.

- Repo: [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)
- The repo does contain a Bun/TypeScript CLI to sync CE plugin configs to other tools (Codex, OpenCode, Gemini CLI, Kiro, Windsurf, OpenClaw). Not a separate plugin — a cross-tool sync utility.
- **Nothing else from Every to install.**

---

## 4. Gap Analysis: Areas Not Yet Covered

### Testing Automation
Currently covered: TDD workflow in superpowers, evals-skills for LLM pipelines. Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `pr-review-toolkit` / `pr-test-analyzer` agent | Checks _behavioral_ coverage vs line coverage; finds critical test gaps in PRs | **Install** — not covered by current stack |
| `0xfurai/claude-code-subagents`: `playwright-expert`, `cypress-expert`, `vitest-expert` | Framework-specific E2E and unit test agents | **Install selectively** — playwright-expert for web testing |
| `shinpr/claude-code-workflows`: `/recipe-add-integration-tests` | Dedicated command to add integration/E2E tests to existing features | **Useful** — explicit integration test recipe |
| `Chat2AnyLLM` collection: `test-writer-fixer`, `api-tester` | Write tests + fix failures; API performance testing | **Moderate** — test-writer-fixer useful for brownfield code |

### CI/CD and Deployment
Currently covered: none dedicated. Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `sgaunet/claude-plugins` → `devops-infrastructure` | Agents: `cicd-specialist` (GitHub Actions, GitLab CI), `aws-specialist`, `devops-specialist` (Terraform/Ansible) | **High value** — fills the CI/CD gap entirely |
| `giuseppe-trisciuoglio/developer-kit` → `developer-kit-aws` | 19 CloudFormation skills (VPC, Lambda, RDS, DynamoDB) + AWS specialists | **Situational** — useful if heavy AWS IaC work |
| `developer-kit-devops` | GitHub Actions + Docker experts | Lighter alternative to sgaunet |
| `0xfurai/claude-code-subagents`: `github-actions-expert`, `terraform-expert`, `kubernetes-expert` | Individual CI/CD and IaC subagents | **Install selectively** — github-actions-expert |

### Database Migrations
Currently covered: none. Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `sgaunet/claude-plugins` → `devops-infrastructure` | `database-specialist` (PostgreSQL/MySQL optimization), `postgresql-specialist` | **Install** as part of devops-infrastructure |
| `hesreallyhim/awesome-claude-code` → `read-only-postgres` | Safe read-only Postgres query skill | **Useful** for exploration/auditing |
| `0xfurai/claude-code-subagents`: `postgres-expert`, `sql-expert` | Postgres and SQL specialists | Standalone agents for on-demand use |

### API Design
Currently covered: none dedicated. Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `0xfurai/claude-code-subagents`: `rest-expert`, `openapi-expert`, `graphql-expert` | REST/OpenAPI/GraphQL specialists | **Install selectively** — openapi-expert most broadly useful |
| `Chat2AnyLLM` collection: `openapi-expert`, `api-integration-specialist` | OpenAPI sync/validation; internal API architecture | Moderate — overlaps with openapi-expert above |

### Documentation Generation
Currently covered: none explicit (compound-engineering has some documentation skills). Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `sgaunet/claude-plugins` → `software-engineering` | `docs-architect` agent for technical documentation | **Install** as part of software-engineering plugin |
| `Chat2AnyLLM` collection: `codebase-documenter`, `changelog-generator` | Full codebase doc generation; automated changelogs | **changelog-generator is genuinely useful** |
| `shinpr/claude-code-workflows`: `/recipe-update-doc`, `/recipe-reverse-engineer` | Update design docs; generate PRDs from existing code | Useful for legacy/undocumented code |

### Monitoring and Observability
Currently covered: none. Gaps:

| Option | What It Adds | Verdict |
|--------|-------------|---------|
| `0xfurai/claude-code-subagents`: `prometheus-expert`, `grafana-expert`, `opentelemetry-expert` | Observability stack specialists | **Situational** — install opentelemetry-expert if instrumenting services |
| `hesreallyhim/awesome-claude-code` → `cc-devops-skills` | DevOps skills with validations, generators for IaC | Complementary to sgaunet devops plugin |

---

## 5. High-Priority Recommendations

### Strong installs (fill real gaps, low cost, no overlap)

1. **`rust-analyzer-lsp`** — `claude-plugins-official`. Real-time Rust diagnostics, go-to-def, find-references. Essential for Rust work. Memory-intensive on large projects — disable if issues arise. Install: `claude.com/plugins/rust-analyzer-lsp`

2. **`hookify`** — `claude-plugins-official`. Create enforcement hooks from markdown config without editing hooks.json. Currently hooks are edited manually; this makes hook iteration dramatically faster. Review: "worth installing now." Install via `/plugin install hookify@claude-plugin-directory`

3. **`skill-creator`** — `claude-plugins-official`. Create/improve/benchmark skills with built-in evals. Given the size of the skills repo and active development, this pays for itself immediately. Install via plugin directory.

4. **`sgaunet/claude-plugins` (devops-infrastructure)** — Fills CI/CD + database gap with: `cicd-specialist`, `aws-specialist`, `database-specialist`, `postgresql-specialist`, `devops-specialist`, `/analyze-db-performance` command. Single plugin install covers three gap areas. [GitHub](https://github.com/sgaunet/claude-plugins)

5. **`pr-review-toolkit`** — `claude-plugins-official`. Agents `silent-failure-hunter` and `pr-test-analyzer` are distinct from compound-engineering's review suite. Catches: silent catch blocks, missing error logging, behavioral test coverage gaps. Additive to, not overlapping with, CE.

6. **Context7 MCP** — Not a plugin but an MCP server. Injects live, version-specific library docs into context. Resolves training data staleness for fast-moving APIs. Free, open-source (Upstash). Install: `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest`. [GitHub](https://github.com/upstash/context7)

### Conditional installs (useful for specific work types)

7. **`pyright-lsp`** — `claude-plugins-official`. Python type checking and go-to-definition. Install if Python work is active (nyx, fasti, agent scripts).

8. **`commit-commands`** — `claude-plugins-official`. `/commit-push-pr` as a single atomic command is cleaner than current ad-hoc commit + PR flows. Low cost, no conflict.

9. **`openapi-expert` subagent** — from `0xfurai/claude-code-subagents`. For REST API design work, OpenAPI spec generation and validation. Drop in as a standalone subagent file to `~/.claude/agents/`.

10. **`playwright-expert` subagent** — `0xfurai` collection. E2E browser testing specialist. Useful when building web tooling or testing agent-browser interactions.

### Skip / deprioritize

- **`ralph-loop`** — **Do not install on Max20.** Multiple reports of wiping weekly quota in a single loop. Quota burn rates 6–60%/hour. The iterative autonomy pattern is covered more safely by strategos + delegating to OpenCode/Codex.
- **`feature-dev`** — Overlaps with strategos + compound-engineering. The 7-phase workflow is largely replicated between those. Only worth it if you prefer a simpler guided mode.
- **`claude-md-management`** — Useful in theory but the CLAUDE.md here is already maintained manually and with write-through-learning discipline. `/revise-claude-md` may add value at session end but competes with `/wrap`.
- **`shinpr/claude-code-workflows`** — Comprehensive but opinionated recipe system. Likely conflicts with strategos + compound-engineering in flow. Evaluate only if strategos is abandoned.
- **`developer-kit` series** — Java/PHP/TypeScript framework-specific. Only relevant if those become primary stacks.

---

## 6. Community Subagent Collections (Drop-in, Not Plugin Install)

These repos ship individual subagent YAML files that can be copied to `~/.claude/agents/` without a full plugin install:

- **`VoltAgent/awesome-claude-code-subagents`** — 100+ agents. Standouts: `sre-engineer`, `chaos-engineer`, `database-optimizer`, `api-designer`. [GitHub](https://github.com/VoltAgent/awesome-claude-code-subagents)
- **`0xfurai/claude-code-subagents`** — Cleaner formatting, better descriptions. All framework experts (jest, vitest, cypress, playwright, prometheus, grafana, opentelemetry, rest, graphql, grpc). [GitHub](https://github.com/0xfurai/claude-code-subagents)

Best approach: cherry-pick specific agents from these repos rather than installing wholesale. Agents to pull:
- `opentelemetry-expert` — if instrumenting any service
- `openapi-expert` — for API contract work
- `playwright-expert` — E2E browser testing
- `github-actions-expert` — CI/CD workflows
- `postgres-expert` — database work

---

## 7. Sources

1. [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) — Official plugin directory
2. [claude-plugins.dev](https://claude-plugins.dev/) — Community registry with CLI
3. [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) — Curated CC resources
4. [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) — 100+ subagents
5. [0xfurai/claude-code-subagents](https://github.com/0xfurai/claude-code-subagents) — 100+ production subagents
6. [Chat2AnyLLM/awesome-claude-plugins](https://github.com/Chat2AnyLLM/awesome-claude-plugins) — 834 plugins, 43 marketplaces
7. [sgaunet/claude-plugins](https://github.com/sgaunet/claude-plugins) — devops-infrastructure + software-engineering + go-specialist
8. [giuseppe-trisciuoglio/developer-kit](https://github.com/giuseppe-trisciuoglio/developer-kit) — Java/TS/Python/AWS/DevOps kits
9. [shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows) — Recipe-based workflows
10. [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) — CE plugin (already installed)
11. [upstash/context7](https://github.com/upstash/context7) — Live docs MCP server
12. [boostvolt/claude-code-lsps](https://github.com/boostvolt/claude-code-lsps) — 23-language LSP collection
13. [Composio: Top 10 Claude Code Plugins](https://composio.dev/content/top-claude-code-plugins)
14. [TurboDocx: Best CC Plugins 2026](https://www.turbodocx.com/blog/best-claude-code-skills-plugins-mcp-servers)
15. [The Register: Ralph Wiggum Loop](https://www.theregister.com/2026/01/27/ralph_wiggum_claude_loops/) — Quota warning context
