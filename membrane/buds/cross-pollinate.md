---
name: cross-pollinate
description: Find a pattern from one domain in vault, apply it to another. Forced analogy engine.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Forced cross-domain pattern transfer. Take a pattern from one domain, apply it elsewhere.

1. Read recent vault content (last 14 days): ~/notes/Daily/ and ~/notes/Inbox/
2. Identify distinct domains in the recent content:
   - System design (vivesca, automation)
   - Consulting / banking
   - Health / physiology
   - Learning / skill acquisition
   - Finance / economics

3. Pick two domains with the most recent thinking — one as SOURCE, one as TARGET

4. Extract the sharpest pattern from SOURCE:
   - A mechanism, a constraint, a failure mode, a design principle
   - Must be specific enough to be non-trivial

5. Apply it to TARGET — force the analogy:
   - Where does it fit cleanly?
   - Where does it break?
   - What does the break reveal about TARGET that wasn't obvious before?

6. Does the insight suggest any concrete change — to vivesca design, consulting approach, personal system?

Output: SOURCE pattern → TARGET application → where it breaks → the insight the break reveals.
2-3 paragraphs. Save to ~/notes/Garden/seeds-cross-pollinate-YYYY-MM-DD.md if the insight is strong.
