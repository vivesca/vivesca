---
name: chemotaxis
description: Peer pattern scanning — systematically scan what peers, competitors, and adjacent practitioners are doing, extract transferable patterns, route to domains (personal stack, consulting, governance). Use monthly as part of /monthly, or ad-hoc when entering a new domain or feeling behind. "What are others doing?", "steal from peers", "landscape scan", "chemotaxis".
user_invocable: true
---

# Specula — Peer Pattern Scanning

From Latin *chemotaxis* — watchtower. Systematic reconnaissance of what peers and competitors are doing, with pattern extraction and domain routing.

## When to Use

- **Monthly** — as part of `/mitosis` review. Scheduled scan of key domains.
- **Ad-hoc** — entering a new domain, starting a new project, feeling behind, or when curiosity strikes. Invoke directly via `/chemotaxis`.

## The Process

### 1. Scope — Pick scan targets

Define WHO to scan and WHAT domain. Examples:

| Domain | Scan targets |
|--------|-------------|
| Personal agent stack | Manus, Devin, Claude Code updates, Cursor, Aider, OpenHands |
| Multi-agent frameworks | AutoGen, LangGraph, CrewAI, Google ADK, OpenAI Agents SDK |
| Consulting AI delivery | McKinsey/BCG/Accenture/Deloitte AI practices, client case studies |
| AI governance | Regulatory guidance, MRM frameworks, NIST/ISO agent standards |
| Productivity systems | Power-user CLI setups, developer tooling trends, PKM innovations |

### 2. Research — Parallel sweep

Launch parallel Sonnet researcher subagents (one per scan cluster). Each researcher:
- Searches blog posts, HN, GitHub, arXiv, leaked prompts, technical deep-dives
- Extracts **patterns**, not products. "What technique makes this work?" not "What does this product do?"
- Structures output as: Pattern name → What problem it solves → How it works → Evidence → How to steal

```
Agent(subagent_type="researcher", model="sonnet", name="chemotaxis-<domain>",
  prompt="Research [targets] for transferable patterns. For each pattern: name, problem solved, how it works, evidence, how to adopt. Structured markdown.")
```

### 3. Synthesize — Extract and route

For each pattern found, classify:

| Tag | Meaning | Routes to |
|-----|---------|-----------|
| `stack` | Improves personal tools/workflow | Skill update, rector task, or direct implementation |
| `capco` | Applicable to consulting delivery | Capco methodology notes, client frameworks |
| `governance` | Relevant to AI governance/MRM | GARP study material, governance frameworks, advisory |
| `universal` | Cross-domain principle | Topica entry, or organon family skill |

### 4. Persist — Write findings

For high-priority patterns tagged `capco` or `governance`, also append to `~/notes/Consulting/_sparks.md` under today's date: `- #[capco|governance] — **[Pattern name]**: [one-line consulting implication]`

Output vault note: `~/notes/Specula/YYYY-MM Peer Scan.md`

Structure:
```markdown
---
date: YYYY-MM-DD
domains: [stack, capco, governance]
---

# Peer Scan — YYYY-MM

## High-Priority Patterns (act on this month)
- Pattern → domain tag → concrete next step

## Medium-Priority (queue for later)
- Pattern → domain tag → what it enables

## Noted but Not Actionable Yet
- Pattern → why it's interesting → what would change to make it actionable

## Sources
- [links]
```

### 5. Action — Create tasks

For high-priority patterns:
- `stack` → add to Praxis.md or create rector task
- `capco` → update methodology notes or client frameworks
- `governance` → update study materials or advisory templates

## Monthly Cadence

In `/mitosis`, chemotaxis runs as one of the review steps:
1. Pick 2-3 domains most relevant to current work
2. Run parallel researchers (~10 min)
3. Synthesize into vault note
4. Create action items for high-priority patterns

## Ad-Hoc Usage

```
/chemotaxis                    # Interactive — pick domains
/chemotaxis agents             # Scan agent engineering specifically
/chemotaxis governance         # Scan AI governance specifically
/chemotaxis consulting         # Scan consulting delivery specifically
```

## Quality Bar

A good chemotaxis scan produces **at least 3 actionable patterns** with concrete "how to steal" steps. If a scan returns only product descriptions or marketing — the researcher prompts need tightening.

## Anti-Patterns

- **Product tourism** — cataloguing tools without extracting patterns. The tool is irrelevant; the technique is the prize.
- **Breadth without depth** — scanning 20 targets shallowly vs 5 deeply. Go deep on fewer.
- **Collecting without acting** — patterns rot if not routed to action. Every high-priority pattern needs a next step.

## Relationship to Other Skills

- **dialexis** — AI landscape awareness for consulting conversations (different purpose: staying current vs pattern extraction)
- **[[analogical-transfer]]** — cross-domain transfer (chemotaxis is same-domain; analogical-transfer is cross-domain)
- **[[mental-models]]** — universal patterns discovered by chemotaxis may become topica entries
