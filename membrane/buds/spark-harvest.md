---
name: spark-harvest
description: Extract consulting sparks from this week's chromatin notes and conversations. Weekly compound machine input.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Harvest consulting sparks from the week's metabolism.

1. Read this week's daily notes: ~/epigenome/chromatin/Daily/YYYY-MM-DD*.md
2. Read this week's chromatin additions: `cd ~/epigenome/chromatin && git log --oneline --since="7 days ago" --name-only`
3. Read recent session context: check ~/epigenome/chromatin/euchromatin/ modified in last 7 days

4. For each note/artifact, ask: is there a consulting-relevant insight here?
   - Banking/fintech application?
   - AI governance angle?
   - Architecture pattern transferable to clients?
   - Risk/compliance implication?

5. Output spark candidates as structured entries:
   - Label: [one-line title]
   - Content: [2-3 sentences, consulting-angled]
   - Tags: [domain tags]

6. Save to ~/docs/sparks/_weekly-harvest-YYYY-WNN.md

This feeds the weekly /expression compound machine.
