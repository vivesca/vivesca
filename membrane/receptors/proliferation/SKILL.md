---
name: proliferation
description: Overproduce skill variants for a domain; let selection pick. Use when entering a new domain and need many skills fast. "proliferate", "skill burst", "adaptive radiation"
effort: high
user_invocable: true
context: fork
---

# /proliferation -- Adaptive Radiation

Rapidly diversify the organism's capabilities for a domain. Overproduce
variants. The selection machinery (integrin) kills what doesn't
earn its place. Design less, produce more, select harder.

## When to Use

- Entering a new domain (new client, new project, new role)
- Organism feels sparse -- too few buds/skills for the work
- "What buds would help here?" -- define 10, let 3 survive
- After a session reveals many manual tasks that could be automated

## Method

### 1. Identify niches

Survey the work domain. What tasks repeat? What could be autonomous?
What needs interactive judgment? What needs coordinated production?

Classify each niche:
- Deterministic reaction → **enzyme** (MCP tool)
- Interactive judgment → **receptor** (skill, process noun)
- Autonomous multi-step → **bud** (agent, phenotype name)
- Coordinated synthesis → **colony** (team template)

### 2. Overproduce

For each niche, define the component. Don't debate quality. Don't
optimize. The minimum viable definition is enough:
- Bud: 15-30 line .md with phenotype name
- Skill: 40-60 line SKILL.md with process noun
- Colony: template with lead + workers + protocol

Target: 2-3x more variants than you think you need.

### 3. Deploy

Commit and push. The variants are now available for metabolism.

### 4. Wait

Let integrin track activation state:
- open (used in 7 days) → surviving
- extended (7-30 days) → marginal
- bent (>30 days) → candidate for retirement

### 5. Cull

Run integrin (apoptosis check). Retire bent variants. Refine survivors.

## Anti-patterns

- **Designing each variant carefully** -- defeats the purpose. Selection is smarter.
- **Keeping everything** -- the point is retirement. If nothing dies, you over-curated.
- **Proliferating without selection** -- useless without integrin.

## Cadence

Run /proliferation when entering a new domain. Monthly cull via
integrin. The germinal center reaction: proliferate → test → select → mature.
