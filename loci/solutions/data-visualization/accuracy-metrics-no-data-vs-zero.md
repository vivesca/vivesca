---
title: "Distinguish 'No Data' from '0%' in Accuracy Metrics"
date: 2026-02-05
category: data-visualization
tags: [metrics, charts, matplotlib, accuracy, feedback]
symptoms:
  - Accuracy chart shows 0% for certain months
  - Misleading drop in accuracy trend line
  - Chart suggests performance crashed when actually no data exists
module: open-webui-db-analyzer
---

# Distinguish "No Data" from "0%" in Accuracy Metrics

## Problem

When plotting accuracy metrics (e.g., thumbs up/down feedback), months with **no feedback data** were displayed as **0% accuracy**. This created misleading charts where the trend line appeared to crash, when the reality was simply "no one rated anything that month."

## Root Cause

The calculation defaulted to 0 when `total_rated == 0`:

```python
# BAD: No distinction between "all negative" and "no data"
acc = (up / total_rated * 100) if total_rated > 0 else 0
```

## Solution

Use `None` for missing data, then filter when plotting:

```python
# GOOD: None signals "no data available"
acc = (up / total_rated * 100) if total_rated > 0 else None

# Filter out None values for line plot
valid_dates = [d for d, a in zip(dates, accuracy) if a is not None]
valid_accuracy = [a for a in accuracy if a is not None]

# Plot only valid points (creates gap in line for no-data months)
ax.plot(valid_dates, valid_accuracy, ...)
```

For data tables, show "N/A" instead of "0%":

```python
if total_rated > 0:
    acc_str = f"{up / total_rated * 100:.1f}%"
else:
    acc_str = "N/A"  # Explicitly signals no data
```

## Why This Matters

| Scenario | 0% Display | N/A Display |
|----------|------------|-------------|
| All feedback negative | Correct | Wrong |
| No feedback at all | **Misleading** | Correct |
| Stakeholder interpretation | "Bot is broken" | "No data yet" |

## Prevention

When building any metric that involves ratios:

1. **Ask:** What does denominator=0 mean?
2. **Distinguish:** "Zero result" vs "No data to compute"
3. **Display:** Use `None`/`N/A`/gap rather than defaulting to 0

## Related

- Tufte's principle: Don't lie with data
- Same pattern applies to: conversion rates, response rates, completion rates
