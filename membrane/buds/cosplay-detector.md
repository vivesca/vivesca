---
name: cosplay-detector
description: Review recent bio-renames and check if each generated a design question. Flag cosplay (label swaps without insight).
model: sonnet
tools: ["Read", "Grep", "Glob", "Bash"]
---

Experiment: audit recent bio-renames for cosplay.

1. Find recent bio-naming changes:
   ```bash
   cd ~/code/vivesca && git log --oneline --since="30 days ago" | grep -i "rename\|bio\|titrat"
   ```

2. For each rename commit, check the diff:
   ```bash
   git show <hash> --stat
   ```

3. For each renamed variable/function/class, apply the cosplay test:
   - Old name: [engineering term]
   - New name: [biological term]
   - Design question generated: [yes/no]
   - If yes: what question? Was it acted on?
   - If no: this is cosplay. Should it be reverted?

4. Compute the cosplay ratio: renames that generated questions / total renames

5. Report:
   - Total bio-renames reviewed: N
   - Genuine titrations: N (with design questions listed)
   - Cosplay: N (with revert recommendations)
   - Cosplay ratio: X% (lower is better)
   - Best rename: [the one that generated the most valuable question]
   - Worst rename: [the most obvious label swap]

Recommended action: revert any rename with cosplay ratio > 30%.

Be honest. The point is to keep the naming discipline honest, not to defend it.
