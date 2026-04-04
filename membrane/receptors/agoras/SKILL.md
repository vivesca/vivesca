---
name: agoras
description: Draft LinkedIn comments and posts. Use when user shares a LinkedIn URL to comment on, says "linkedin comment", "linkedin post", or wants to draft/post content.
user_invocable: true
---

# LinkedIn Skill

Draft comments on others' posts and original posts for Terry's LinkedIn.

## Triggers

URL-based triggers are handled by the `url-skill-router` hook (auto-injects reminder on LinkedIn URLs).
Keyword triggers: "linkedin", "comment on this", "should we comment", "draft a post", "post about X".

## Mode Detection

| Signal | Mode |
|--------|------|
| URL shared or "comment on" | **Comment** |
| "draft post", "post about", or topic from Content Ideas | **Post** |

---

## Comment Mode

### 1. Fetch the Post

LinkedIn is login-gated. Always use authenticated browser:

```bash
agent-browser open "<url>" --profile
agent-browser snapshot --profile
agent-browser close --profile
```

Extract: author name/title, verbatim post text, all comments (author + text), engagement counts.

### 2. Research the Author

**Check vault first.** Profiles are cached at `~/epigenome/chromatin/LinkedIn Profiles/<Name>.md`. Check before fetching LinkedIn:

```bash
ls ~/epigenome/chromatin/LinkedIn\ Profiles/
# look for <Name>.md — if found, read it
```

If a cached profile exists and was updated within 90 days, use it and **skip the LinkedIn experience fetch entirely**. The cached file includes career history, relationship context, and engagement history.

If no cached profile (or >90 days old): fetch the full experience page — the main profile truncates roles. Navigate to `/details/experience`, not just `/in/<username>`:

```bash
agent-browser open "https://www.linkedin.com/in/<username>/details/experience" --profile
agent-browser snapshot --profile
```

Key things to surface: prior companies, domain expertise accumulated before current role, any FS/banking background. This prevents explaining someone's own domain back to them.

**After researching, save or update the vault profile:**

```bash
# Create or overwrite ~/epigenome/chromatin/LinkedIn Profiles/<Name>.md
```

Profile format:
```md
---
type: linkedin-profile
name: <Full Name>
url: https://www.linkedin.com/in/<username>
last_updated: <YYYY-MM-DD>
---

# <Full Name>

**Current:** <role> at <company>
**Relationship:** <how connected to Terry — former colleague, 1st connection, potential Capco client, etc.>

## Career History
- <Company> — <role> (<years>)
- ...

## Engagement History
- <YYYY-MM-DD>: Commented on "<post topic>" — <one-line summary of what Terry said>
```

Add each new comment to the Engagement History section after posting. This log replaces `anam search` for frequent contacts.

### 3. Assess: Should Terry Comment?

Answer these before drafting:

1. **Is the topic in Terry's lane?** (AI, financial services, governance, enterprise tech, consulting)
2. **Can Terry add a distinct angle?** (Not just agreement — a practitioner insight, extension, or counterpoint)
3. **Is the author worth engaging?** (Senior practitioner, potential client/referral, thought leader in FS/AI)
4. **Is the timing right?** LinkedIn's algorithm weights first-hour engagement most heavily — a post >24h old has already peaked in distribution. But timing affects *reach*, not whether the poster sees it — LinkedIn notifies authors of every comment regardless of age. So: >48h is fine if the author is a high-value target (senior FS exec, potential Capco client) and the post has low engagement (<50 reactions) — they'll notice and appreciate it. Skip only if the post is >1 week old or already has 100+ comments. Check the vault profile's Engagement History — if Terry commented on this person in the last 7 days, skip. Fallback: `anam search "<author>" --deep`.
5. **Is the post worth Terry's comment?** If Terry's comment would be smarter than the post itself, react and move on. Comment when the post pulls the conversation *up* — original frameworks, genuine depth, substantive takes. Skip well-packaged platitudes, repackaged concepts, and content-mill series. Terry's practitioner insights should add to something strong, not carry something thin.
   **High-frequency poster signal:** If a connection has recently shifted to posting every 1-2 days with consistent format and recurring themes, check whether insight-per-post is diluting. High volume + uniform structure + checklist content = likely AI-generated cadence. Downgrade engagement threshold: only comment when there's a specific structural claim worth extending. In practice this means once a month at most, regardless of posting frequency. Use as a negative example for Terry's own cadence — low frequency, high specificity is the counter-model.
6. **Will the poster be happy to see this comment?** Read the emotional register of the post. If they wrote an enthusiasm/vision post, a purely risk-focused or corrective comment lands as a buzzkill — even if factually additive. The comment should match or gently extend the poster's tone, not deflate it. A cold commenter who makes a CIO look behind on risk management in front of their peers is not welcome. If the honest angle is negative, consider liking and moving on instead.

If any answer is no, say so and suggest skipping or just reacting.

### 4. Find Terry's Angle

**The frame: Echo + Extend.** The best comment echoes what the poster said (makes them feel heard) then extends it with one specific insight they didn't name. Not a new topic — an extension of their exact point.

**Post quality check — before finding an angle, assess the post critically:**
- Is there a genuinely distinctive insight to echo, or is it a solid synthesis of conventional wisdom?
- Common false positives: banking controls doctrine (maker/checker), consulting truisms (operating model vs technology upgrade), standard checklist items (include compliance costs in the business case). These feel specific but aren't sharp.
- If no single insight stands out as distinctive: don't force it. Use the "thank you for this — particularly X" pattern (see Step 5) — generic warmth rescued by a specific point.

**Finding the DS add — look for the unstated dual function or secondary mechanism.** When a poster names a role or concept (e.g. "checker role"), ask: does this role serve a second function they didn't name? A concept often has a primary use (what the poster said) and a secondary mechanism (what the data layer sees). That gap is usually where the genuine DS contribution lives. Example: "checker role" = quality control (Gary's framing) + data labeling (DS framing the poster left implicit).

**Technical claim stress-test — before including any DS claim, ask three questions:**
1. Is this from Terry's actual lane (data science / ML), not the poster's domain (ops, compliance, IT)?
2. Does it apply to the full scope the poster describes — or only one part of their progression?
3. Would a domain expert push back on this? If yes, drop it or narrow the claim.

**Brainstorm method:** Map the poster's actual claims (list them), then ask:
- What did they almost say but didn't?
- What's the next logical step they left implicit?
- What does *Terry's specific lane* (AI/data science) see that they didn't name?
- What external signal (regulatory, industry) confirms their thesis?

When stuck on angle, run `consilium` with the post + Terry's constraints explicitly — ask for 3-4 distinct angles with one-line drafts. Don't iterate on a bad angle; find the right angle first.

Terry's strongest angles (in order of preference):

1. **Make their urgency more concrete** — they said "now matters"; add *why* now, with a specific mechanism or example
2. **Validate their call-to-action with a specific constraint** — "you're right to say prepare today; here's the bottleneck most miss"
3. **Bridge from Terry's lane to their thesis** — what does the AI/data layer see that the poster's framing didn't cover? (e.g. if post is about security: "the data our models train on is protected by the same encryption quantum threatens")
4. **The regulatory/institutional signal** — "the regulators are also moving on this" — echoes their thesis with external confirmation
5. **Echo their opening with an irony or tension they didn't name** — extends their frame without leaving it

**For senior practitioners (any relationship):** the "I learned X from you" pattern is the most natural register — it's warm without grading, and specific > generic. Structure: name + thanks → name exactly what you learned (one phrase, specific) → add from your own lane. Example: "Gary, thanks — [specific reframe] is the reframe I didn't know I needed. From the data science side, [DS add]." Address by first name at the start; it signals genuine engagement, not a broadcast comment. The specific learning must be named — vague "this reframed how I think" is as hollow as "very insightful."

**When the poster is more senior (GM, MD, Partner, CIO):** contribute as a supplemental observation from your lane only — never implicit design advice or recommendations in their domain. Frame as "from the data science side, [observation]" not "you should design X" or "only if Y is built in." The caveat test: if your closing sentence implies the poster needs to do something differently, reframe it as an observation or drop it.

Check vault for supporting material:

```bash
cerno "<topic>"
```

Draw from real experience (CNCBI governance, HKMA sandbox, AML model, agent architecture) — never fabricate.

### 5. Draft the Comment

**Voice rules** (rationale: `[[LinkedIn Commenting Principles]]`)**:**
- **No grading openers** — banned: "Great call", "Spot on", "Exactly right", "Well said", "You're right to", "Sharp", "Right starting point" — all put Terry in the judge seat. Use peer-level observation or lead directly from Terry's lane instead.
- **"Yes-and", never "yes-but"** — extend their thesis, don't redirect it
- **Match the poster's emotional register** — measured post → measured comment, no injected optimism
- **Never raise corrections or risks unless explicitly invited**
- **For senior practitioners:** "I learned X from you" pattern — name + thanks → specific learning (named, not vague) → add from Terry's lane
- "I've seen" not "I'd add" (observational, not prescriptive)
- Specific > generic (name the committee, the system, the failure mode)
- Stress-test any technical claim — if a domain expert would push back, drop it
- No hashtags, no "great post!", no engagement bait
- Spelling: British for UK/HK/APAC authors, US for US-based
- Plain text only — LinkedIn comments don't support markdown
- ~50-70 words, minimum 15 words, 4-8 sentences max

**Structure:**
1. Brief validation (one phrase, specific — not "great post")
2. The insight (1-2 sentences — the practitioner pattern)
3. Concrete illustration (the vivid contrast or example)
4. Implication (why this matters — the "so what")
5. Optional: closing observation (not a question demanding disclosure)

**When there's no single profound insight to call out:** Use "thank you for this — particularly [specific point]" — generic warmth rescued by a specific point that proves you read it. The specific point does the work; the warmth is just the frame. Example: "Gary, thank you for this — particularly the accuracy-improves-progressively point. From the data science side, [add]." Don't try to call something "sharp" or "insightful" if it isn't — the specific point is enough.

**Stay in the poster's thesis.** The comment should extend *their* point, not introduce a third topic they didn't raise. If the post is about encryption risk, respond to encryption risk — don't pivot to ML infrastructure overhead just because it's related to quantum. Adjacent ≠ responsive. Check: does the comment answer the question the poster was implicitly asking?

**Complement check.** Before presenting the draft, ask: would a reader skimming both the post and this comment see the thread clearly? The comment should visibly connect — echo a specific word, phrase, or idea from the post before adding from Terry's lane. If the comment could have been written without reading the post, it's not complementing — it's broadcasting.

**Iteration note.** Consilium is better at catching what's wrong than finding the right voice. After the council review, expect to iterate on tone, structure, and connection to the post through back-and-forth — that loop does more work than the upfront council. Don't treat the council draft as final.

**Time budget.** A LinkedIn comment should take 20-30 minutes total. One council run, then direct iteration with Terry. Stop when it passes the stress-tests — not when it feels perfect. LinkedIn comments have a 24h relevance window; perfect is the enemy of posted. If iteration has gone past 3 rounds after the council, call it and post. Remind Terry of this explicitly if the loop is running long.

Present the draft in chat with a one-line rationale for the angle chosen. **Stop here and wait for input.**

### 6. Consilium Review (mandatory for all comments)

All comments get `--deep` consilium before finalising — comments are public and reputation-building.

Run automatically (no need to ask): provide full post context (verbatim text, all comments, author background) — never summarise the post for the council.

Always include the voice rules AND review criteria in the prompt:

```
VOICE RULES (Terry's LinkedIn commenting style):
- "Yes-and", never "yes-but" — extend the thesis, don't redirect it
- No grading openers — banned: "Exactly right", "Great call", "Spot on", "You're right to", "Well said", "This is exactly the point". Anything that evaluates whether the poster got it correct is a grading move.
- For senior practitioners: "I learned X from you" pattern works well — name + thanks → specific learning (one phrase) → add from Terry's lane. The specific learning must be named; vague "this reframed how I think" is hollow.
- Address by first name at the start — signals genuine engagement, not a broadcast
- Match the poster's emotional register — measured post → measured comment, no injected optimism
- Add something the poster didn't say — don't restate their own points back to them
- End with an observation, not a question
- ~50-70 words, plain text, British spelling

REVIEW CRITERIA:
1. Does the comment extend the poster's thesis without redirecting it?
2. SENIORITY CHECK: Does the opener put Terry in the judge seat? Flag and suggest rewrite if present.
3. Does it avoid repeating points the poster already made?
4. Does it avoid yes-but / correction patterns?
5. Does it match the poster's emotional register?
6. Is the angle from Terry's lane (AI/data science), not the poster's domain?
7. Does the comment clearly connect back to the post — would a reader who skims both see the thread?
```

### 7. Finalise and Deliver

Once Terry approves the draft, **gist it for mobile copy-paste** and **like the post automatically**. Terry posts the comment manually — comments are public and permanent, final eyes-on before submitting is worth the extra step.

```bash
# Gist the draft — include verbatim post for mobile context check before pasting
gh gist create --public=false -f "linkedin-comment.md" - << EOF
## Post — <Author Name>
<post URL>

<verbatim post text>

---

## Draft Comment — Terry Li
<comment text>
EOF

# Like the post
agent-browser click <react-like-ref> --profile
agent-browser close --profile
```

After Terry confirms posted, **update the vault profile's Engagement History**:

```bash
# Append to ~/epigenome/chromatin/LinkedIn Profiles/<Name>.md Engagement History
# - <YYYY-MM-DD>: Commented on "<topic>" — <one-line summary>
```

Then delete the gist.

```bash
gh gist create --public=false -f "linkedin-review.md" - << EOF
## Original Post — <Author Name>

<post URL>

<verbatim post text>

---

## Draft Comment — Terry Li

<draft comment text>
EOF
```

When posting the comment via agent-browser, also like the post — it's basic engagement hygiene:

```bash
# After filling and submitting the comment box:
agent-browser click <like-button-ref> --profile
```

The Like button ref is typically labelled "React Like" in the snapshot. Click it before closing the browser. Delete gist after Terry confirms it's copied.

---

## Post Mode

### 1. Check Content Ideas (MANDATORY — do not skip)

**Every LinkedIn post draft MUST have an entry in `[[LinkedIn Content Ideas]]` BEFORE any draft file or gist is created.** This is the single source of truth for the content pipeline.

```bash
cat ~/epigenome/chromatin/LinkedIn\ Content\ Ideas.md
```

If the topic exists, use the captured angle/details. If new, add the entry first (hook, angle, status, timing gate), then create the draft file linked from it.

**Bidirectional linking is mandatory:** hub entry → `[[Draft Note]]` AND draft note's Related field → `[[LinkedIn Content Ideas]]`. Both directions, always.

### 2. Draft Against Playbook Rules

Read the playbook: `~/epigenome/chromatin/LinkedIn Posting Playbook.md`

**Hard rules:**
- No external links in post body (link goes in first comment)
- Don't undersell — "system" not "script" when architecture warrants
- Add a visual recommendation (screenshot, diagram, architecture)
- One solid post per 2-3 weeks cadence
- **Write in prose, not lists.** Terry's default is flowing paragraphs. No numbered headers, no bullet points. Bold lead sentences are fine for scannability but structure should come from paragraph breaks, not list formatting.

**Post types:**
- "I built X" — credibility through shipping
- "I learned X" — LinkedIn algo loves learning narratives
- "Observation from the field" — Capco-era content (post Mar 16)

**Timing gate:**
- Posts that need "AI Solution Lead" title weight → after Capco start (Mar 16+)
- Builder/personal posts → anytime

### 3. Censor Review (first pass)

Run censor with `linkedin-post` criteria before spending on consilium:
- If `needs_work`: revise and re-censor (max 1 iteration)
- If `pass`: proceed to consilium

### 4. Consilium Review

All posts get consilium `--council` (~$0.50) — posts are public and reputation-building, `--quick` doesn't catch tone/positioning risks. High-stakes posts (first Capco-era, controversial angle) get `--deep` (~$0.90) or `--redteam` (~$0.20) to stress-test the angle.

### 5. Deliver

Gist the draft for mobile:

```bash
gh gist create --public=false -f "linkedin-post.md" - <<< "<post text>"
```

Update `[[LinkedIn Content Ideas]]` status to "Draft ready" with date.

---

## Pre-Capco vs Post-Capco

| Timing | What's safe | What to avoid |
|--------|------------|---------------|
| **Now (pre-Mar 16)** | Builder proof, personal stories, practitioner comments | "As an AI Solution Lead at Capco..." |
| **Post-Mar 16** | Enterprise diagnostics, consulting frameworks, client-ready insights | Mentioning specific client names |

## Vault References

- `~/epigenome/chromatin/LinkedIn Content Ideas.md` — content pipeline
- `~/epigenome/chromatin/LinkedIn Posting Playbook.md` — positioning, metrics, cadence
- `~/epigenome/chromatin/LinkedIn Commenting Principles.md` — rationale behind the voice rules
- `~/epigenome/chromatin/LinkedIn Profile Updates - Feb 2026.md` — headline/about copy
- `~/epigenome/chromatin/LinkedIn Profiles/` — cached author profiles
- `~/epigenome/chromatin/Councils/LLM Council - LinkedIn*` — past comment/post reviews
