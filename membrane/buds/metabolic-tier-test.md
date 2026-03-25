---
name: metabolic-tier-test
description: Test if metabolic tiers are working -- did behavior change when budget shifted? Was tier guidance followed?
model: sonnet
tools: ["Read", "Grep", "Bash"]
---

Experiment: test the metabolic tier system.

1. Read current allostasis state:
   ```bash
   cat ~/.local/share/respirometry/budget-tier.json
   ```

2. Read the tier history from today's session:
   ```bash
   grep -i "metabolic\|anabolic\|homeostatic\|catabolic\|autophagic\|allostasis\|budget" ~/.claude/tool-call-log.jsonl | tail -20
   ```

3. Check if tier-appropriate behavior was followed:
   - During anabolic: were opus subagents used? Creative exploration?
   - During homeostatic: were sonnet subagents preferred?
   - During catabolic: was effort reduced? Single approaches?
   - During autophagic: did the session checkpoint and stop?

4. Check for tier violations:
   - Opus subagent dispatched during catabolic/autophagic?
   - Exploratory research during catabolic?
   - No effort reduction when indicated?

5. Report:
   - Tiers encountered this session: [list]
   - Tier transitions: [from -> to, with trigger]
   - Compliance: [followed / violated + details]
   - Recommendation: adjust thresholds? Change guidance text?

This is observational -- measure, don't change.
