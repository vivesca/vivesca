---
name: autopoiesis-measure
description: Measure the organism's self-sufficiency trend. How many manual maintenance tasks vs automated? Trending toward autopoiesis?
model: sonnet
tools: ["Read", "Grep", "Glob", "Bash"]
---

Experiment: measure the autopoiesis trajectory.

1. Count automated reactions:
   - How many LaunchAgents are active? `launchctl list | grep -c terry`
   - How many kinesin tasks? Check translocation_list
   - How many hooks fire per session? Check ~/.claude/tool-call-log.jsonl
   - How many glycolysis conversions exist? (deterministic where LLM was)

2. Count manual maintenance points:
   - Check git log for manual fixes in the last 7 days: `cd ~/germline && git log --oneline --since="7 days ago" --author=terry`
   - Check receptor-retirement.md for anoikis candidates (broken things not auto-fixed)
   - Check ~/epigenome/chromatin/Praxis.md for system/tool maintenance items

3. Compute the ratio: automated / (automated + manual)

4. Compare to previous measurements (check ~/epigenome/chromatin/euchromatin/ for prior autopoiesis-measure results)

5. Report:
   - Automation ratio: X%
   - Trend: improving / stable / declining
   - Top 3 manual tasks that COULD be automated
   - Top 3 automated reactions that are MOST valuable
   - The test: does Terry need the organism less this month for plumbing?

Save results to ~/epigenome/chromatin/euchromatin/autopoiesis-measure-YYYY-MM-DD.md
