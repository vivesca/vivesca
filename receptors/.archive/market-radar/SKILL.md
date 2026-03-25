---
name: market-radar
description: Detect roles before posted via signals. Monitor earnings calls, leadership changes, funding, and regulatory signals to predict hiring. Triggers on "market-radar", "what's coming", "predict roles".
---

# Market Radar

Detect hiring opportunities before they're posted by monitoring predictive signals.

## Purpose

Public job postings are lagging indicators. Leading indicators include:
- **Earnings calls**: "Investing in AI capabilities"
- **Leadership changes**: New CDO/CTO/CIO typically hires within 90-180 days
- **Funding**: Series B+ triggers expansion
- **Regulatory**: New rules create compliance hiring
- **Network intel**: Informal signals from contacts

This skill monitors and interprets these signals.

## Trigger

Use when:
- User says "market-radar", "what's coming", "predict roles"
- Weekly reset (scan for new signals)
- Specific company research
- Processing news or earnings info

## Inputs

- **mode**: "scan" (check all sources) | "add" (new signal) | "research" (specific company)
- **company** (for research/add): Company name
- **signal** (for add): Signal details

## Workflow

### Mode: Scan

1. **Check signal sources**:

   **Earnings/Announcements** (via web search):
   - Search: "[company] AI investment 2026"
   - Search: "[company] digital transformation hiring"
   - Search: "[company] data science team expansion"

   **Leadership Changes** (LinkedIn/news):
   - New CDOs, CTOs, CIOs at target companies
   - Cross-reference with [[HM Tracker]]

   **Funding** (via web search):
   - Recent Series B+ rounds in Hong Kong fintech
   - "AI startup funding Hong Kong 2026"

   **Regulatory** (HKMA, SFC):
   - New guidance or requirements
   - Compliance deadlines

   **Network Intel**:
   - Check [[Market Radar]] for logged intel
   - Review recent recruiter conversations

2. **Compile signals**

3. **Predict roles**:
   For each signal, predict:
   - Role type likely created
   - Timing (immediate, 3 months, 6 months)
   - Confidence level

4. **Update [[Market Radar]]**

### Mode: Add

1. **Capture signal**:
   - Source type
   - Company
   - Signal details
   - Date observed

2. **Predict implications**:
   - What roles will this create?
   - When?
   - How to position for them?

3. **Update [[Market Radar]]**

### Mode: Research (Specific Company)

1. **Deep scan**:
   - Recent earnings/investor calls
   - Leadership changes past 6 months
   - Funding history
   - Hiring patterns (job posting history)
   - News mentions

2. **Synthesize hiring outlook**

## Output

**Scan Mode:**
```markdown
# Market Radar Scan — [Date]

## New Signals Detected

### Earnings/Announcements
| Company | Signal | Source | Predicted Role | Timing |
|---------|--------|--------|---------------|--------|
| [Company] | [Signal] | [Source] | [Role] | [When] |

### Leadership Changes
| Company | Person | New Role | Start | Hiring Window |
|---------|--------|----------|-------|---------------|
| [Company] | [Name] | [Role] | [Date] | [90-180d from start] |

### Funding
| Company | Round | Amount | Date | Likely Hires |
|---------|-------|--------|------|--------------|
| [Company] | [Round] | [Amount] | [Date] | [Roles] |

### Regulatory
| Regulation | Effective | Impact | Roles Created |
|------------|-----------|--------|---------------|
| [Reg] | [Date] | [Impact] | [Roles] |

## Actionable Insights

1. **[Company]**: [Signal] suggests they'll hire [Role] in [Timeframe]. Consider: [Action]
2. ...

## Updated [[Market Radar]]
```

**Research Mode:**
```markdown
# Market Intel: [Company]

## Recent Activity
- **Earnings**: [Summary]
- **Leadership**: [Changes]
- **Funding**: [Status]
- **Hiring patterns**: [Job posting trends]

## Hiring Outlook
- **Likely roles**: [Predictions]
- **Timing**: [When]
- **How to position**: [Strategy]

## Suggested Actions
1. [Specific outreach or monitoring]
```

## Signal Interpretation Guide

| Signal | Typical Lag | Confidence |
|--------|-------------|------------|
| "Investing in AI" (earnings) | 3-6 months | Medium |
| New CDO/CTO hired | 3-6 months | High |
| Series B+ funding | 1-3 months | High |
| New regulation announced | 6-12 months | Medium |
| "Hiring data scientists" (press) | Immediate | High |

## Integration

- **`/weekly-reset`**: Auto-scans for new signals
- **`/evaluate-job`**: Cross-reference with known signals
- **[[HM Tracker]]**: Leadership changes feed both

## Examples

**User**: "market-radar"
**Action**: Scan all signal sources, compile predictions
**Output**: Signal summary with actionable insights

**User**: "What's the hiring outlook for Manulife?"
**Action**: Deep research on Manulife signals
**Output**: Company-specific intel and predictions

**User**: "I heard DBS is investing heavily in AI — add that as a signal"
**Action**: Log signal, predict implications
**Output**: Confirmation with role predictions
