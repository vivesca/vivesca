---
name: garden-ideas
description: Extract publishable ideas from week's chromatin + conversations. Garden-ready.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Harvest ideas worth publishing to the digital garden from the week's thinking.

1. Read this week's daily notes: ~/epigenome/chromatin/Daily/ (last 7 days)
2. Check recent chromatin additions: `cd ~/epigenome/chromatin && git log --since="7 days ago" --name-only --format=''`
3. Read ~/epigenome/chromatin/Inbox/ for any unprocessed captures

4. For each note/fragment, test against three filters:
   - Is there a transferable insight here? (not just personal logistics)
   - Could a stranger benefit from reading this?
   - Is it specific enough to be non-obvious?

5. For qualifying ideas, draft a garden-ready seed:
   - Title (plain, no cleverness)
   - 2-3 sentences of core insight
   - One concrete example or application
   - Tags: [domain, format-hint]

6. Flag format hint: tweet / short-post / long-form / thread

Output: list of 3-7 seeds. Save to ~/epigenome/chromatin/Garden/seeds-YYYY-WNN.md.
Quality over quantity — 3 strong seeds beats 10 weak ones.
