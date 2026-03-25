# Agent Autonomy: Empirical Findings (Anthropic, Feb 2026)

Source: https://www.anthropic.com/research/measuring-agent-autonomy

Study of millions of human-agent interactions across Anthropic's public API and Claude Code.

## Key Findings

### 1. Experienced users supervise differently, not less
- New users: ~20% auto-approve, ~5% interrupt rate
- Experienced users: ~40% auto-approve, ~9% interrupt rate
- The paradox: more trust AND more interrupts = strategic monitoring replaces action-by-action gating

### 2. Agents self-regulate more than humans
- Claude Code requests clarification 2x+ more than humans interrupt
- Breakdown: approach choices (35%), diagnostics gathering (21%), credential requests (12%)
- Counter-narrative to "agents run wild" — useful for policy/compliance conversations

### 3. Risk and autonomy are orthogonal
- High-autonomy tasks can be low-risk (system monitoring)
- Low-autonomy tasks can be high-risk (medical records retrieval)
- Most governance frameworks implicitly assume correlation — this data says otherwise

### 4. Autonomy duration is growing steadily
- 99.9th percentile turn duration: ~25 min (Oct 2025) → ~45 min (Jan 2026)
- Driven by user trust + product design, not just model capability

### 5. Current deployments cluster low-risk
- 80% of tool calls include safeguards
- 73% maintain human involvement
- Only 0.8% are irreversible (e.g. customer emails)
- Software engineering = ~50% of all agentic activity

## Policy Implication

Don't mandate specific interaction patterns (human approval per action). Focus on whether humans *can* effectively monitor and intervene. Monitoring-based oversight > gate-based oversight.

## Consulting Relevance

- The interrupt paradox is a strong talking point: "mature AI adoption means smarter oversight, not more oversight"
- Risk/autonomy decoupling argues for risk-based governance frameworks, not blanket autonomy limits
- The 0.8% irreversible stat is useful for calibrating client anxiety about agent deployments
- Agent self-regulation data supports building AI systems that surface uncertainty rather than proceeding blindly
