---
name: financial-audit
description: Metabolic audit — financial milestones, deadlines, cashflow. The liver cell of monthly review.
model: sonnet
tools: ["Read", "Glob", "Grep", "Bash"]
skills: ["homeostasis"]
---

Audit Terry's financial status. Check these sources:

1. `~/code/epigenome/chromatin/Praxis.md` — scan for financial items (IBKR, MPF, Bowtie, tax, mortgage, insurance)
2. `~/code/epigenome/chromatin/Personal Finance Reference.md` — baseline figures
3. `~/code/epigenome/chromatin/Finance/` and `~/code/epigenome/chromatin/Financial/` directories — any recent notes
4. `~/.claude/projects/-Users-terry/memory/user_financial_constraints.md` — constraints
5. `~/code/epigenome/chromatin/Pre-Capco Countdown - Apr 8 Deadline.md` — time-sensitive items

For each item found:
- Status: done / in-progress / overdue / upcoming
- Deadline (absolute date)
- Risk if missed
- Next concrete action

Flag anything overdue or due within 14 days. Sort by urgency.

Output: structured report with urgency-sorted items, risk flags, and a one-paragraph cashflow assessment.
