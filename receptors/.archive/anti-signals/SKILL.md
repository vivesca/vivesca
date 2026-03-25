---
name: anti-signals
description: Learn YOUR false positives from rejections. Run to analyze rejection patterns and integrate with /evaluate-job. Use when reviewing rejections or after "anti-signals", "rejection patterns".
---

# Anti-Signals

Analyze rejection patterns to detect personal false positives — roles that look good on paper but consistently lead to rejection for YOU.

## Purpose

Not all rejections are random. Some reveal systematic patterns:
- Certain companies repeatedly reject you
- Specific role types don't convert
- Particular requirements correlate with rejection

This skill detects those patterns and integrates with `/evaluate-job` to warn before applying.

## Trigger

Use when:
- User says "anti-signals", "rejection patterns", "why do I keep getting rejected"
- Periodic review (monthly)
- After significant rejection to check if it fits a pattern

## Workflow

1. **Read rejection data**:
   - [[Job Hunting]] → "Passed On" section (rejections by company)
   - [[Job Hunting]] → "Applied Jobs" section (look for rejection notes)
   - Grep for "rejected", "passed", "didn't proceed"

2. **Analyze patterns**:

   **By Company:**
   | Company | Rejections | Roles | Pattern? |
   |---------|------------|-------|----------|
   | AIA | 3+ | Principal levels | Yes — consistent |
   | Binance | 1 | Head of DS | Maybe — too few data points |

   **By Role Type:**
   | Role Type | Applied | Rejected | Rate | Pattern? |
   |-----------|---------|----------|------|----------|
   | Product Manager | 0 | N/A | N/A | N/A (not applying) |
   | Data Architect | 2 | 1 | 50% | Insufficient data |

   **By Requirement:**
   | Requirement | Appeared In | Rejected | Correlation |
   |-------------|-------------|----------|-------------|
   | "Master's/PhD required" | 5 | 4 | High |
   | "10+ years experience" | 8 | 3 | Medium |

3. **Identify confirmed patterns** (3+ data points, >50% rejection rate)

4. **Update Anti-Signals section** in [[Job Hunting]]

5. **Generate integration rules** for `/evaluate-job`

## Output

**Template:**
```markdown
# Anti-Signal Analysis — [Date]

## Confirmed Patterns (High Confidence)

| Pattern | Evidence | Rejection Rate | Recommendation |
|---------|----------|----------------|----------------|
| [Pattern] | [Examples] | [X/Y] | PASS or FLAG |

## Emerging Patterns (Monitor)

| Pattern | Evidence | Rejection Rate | Notes |
|---------|----------|----------------|-------|
| [Pattern] | [Examples] | [X/Y] | Need more data |

## Updated Rules for /evaluate-job

When evaluating roles, check for these patterns and adjust:
1. [Pattern] → Downgrade APPLY to CONSIDER
2. [Pattern] → Add warning to recommendation

## Expired Patterns (Review)

Patterns that may no longer apply:
- [Pattern] — Last rejection [Date], consider removing if no new data
```

## Integration with /evaluate-job

When `/evaluate-job` runs:
1. After fit analysis, check Anti-Signals section in [[Job Hunting]]
2. If role matches a pattern, add warning:
   ```
   ⚠️ ANTI-SIGNAL: This matches your [pattern] rejection pattern.
   Evidence: [X] of [Y] similar roles rejected.
   Consider: Applying anyway (thin pipeline) or PASS (healthy pipeline)
   ```
3. Factor into final recommendation

## Error Handling

- **Too few rejections**: Note insufficient data for pattern detection
- **No patterns found**: Good news — rejections may be random
- **Conflicting patterns**: List both, note uncertainty

## Examples

**User**: "anti-signals"
**Action**: Scan rejection data, analyze patterns, update Job Hunting.md
**Output**: Pattern analysis with confirmed and emerging patterns

**User**: "Why do AIA keep rejecting me?"
**Action**: Focus on AIA rejections, analyze common factors
**Output**: Specific AIA pattern analysis and recommendation
