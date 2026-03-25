---
name: capco-prep
description: "Capco onboarding readiness — drill, brief, or event-specific prep. 'capco prep', 'capco drill', 'capco brief'"
user_invocable: true
model: sonnet
status: retiring
retire_after: 2026-04-08
---

# Capco Readiness

Three modes for Capco onboarding prep before start (Apr 8, 2026 — confirmed).

**Primary client context:** HSBC is the anchor account for Terry's placement. Key contacts: Simon Eltringham and Tobin Joseph. See [[Capco Day 1 Strategy]], [[Simon Eltringham - HSBC Profile]], [[Tobin Joseph - HSBC Profile]].

**Model: Sonnet.** Brief and prep modes need web search + synthesis. Drill mode is simple but keeping one model for the whole skill. see [[mental-models]] for consulting-relevant models (automation bias, Goodhart's, principal-agent) when framing scenarios.

## Trigger & Modes

| Invocation | Mode | What it does |
|---|---|---|
| `/capco-prep` or `/capco-prep 3` | **drill** | Active recall quiz (default 3 questions) |
| `/capco-prep brief` | **brief** | Pull-based reading recs + actionable prep item |
| `/capco-prep prep <event>` | **prep** | Meeting-specific prep (e.g., "prep coffee with Simon") |
| `/capco-prep status` | **status** | Progress dashboard: drill coverage, weak spots |

Default (no args) = **drill** mode.

## Data

- **Questions:** `~/code/vivesca-terry/chromatin/Capco/Capco Readiness Drill.md` — 40 numbered questions in 7 categories (A-G): tiering framework, regulatory landscape, AI/FS knowledge, consulting delivery, Capco culture, client questions (HSBC context), personal narrative
- **State:** `~/code/vivesca-terry/chromatin/Capco/.capco-drill-state.json` — drill history and ratings
- **Reference:** Questions link to source material in `~/code/vivesca-terry/chromatin/Capco/` — read if user asks "what's the answer?"
- **Verbal Narrative Bank:** `~/code/vivesca-terry/chromatin/Capco/Verbal Narrative Bank.md` — practiced narratives for client and team introductions
- **Client First Meeting Cheat Sheet:** `~/code/vivesca-terry/chromatin/Capco/Client First Meeting Cheat Sheet.md` — HSBC-specific first impression guide
- **90-Day Scorecard:** `~/code/vivesca-terry/chromatin/Capco/90-Day Success Scorecard.md` — success metrics and gates for first 90 days

## Workflow

### 1. Load State

Read `~/code/vivesca-terry/chromatin/Capco/.capco-drill-state.json`. If it doesn't exist, create it:

```json
{
  "drills": {},
  "sessions": 0,
  "last_session": null
}
```
If read fails due corruption, back up the bad file and recreate from default state.

Where `drills` maps question numbers (strings) to:
```json
{
  "last_drilled": "2026-02-21",
  "rating": "shaky",
  "times_drilled": 2
}
```

### 2. Pick Questions

Select N questions (default 3) using this priority:

1. **Never asked** — questions with no entry in `drills` (pick randomly)
2. **Rated "blank"** — couldn't articulate at all (highest priority for repeat)
3. **Rated "shaky"** — partial articulation, needs practice
4. **Least recently drilled** — among "confident" questions, pick the oldest
5. **Random** — if all questions are recently drilled and confident

Ensure no two questions from the same category (A-G) in one session when possible.

### 3. Present Questions

Read the question bank file. For each selected question:

1. Show the **category letter and question number** (e.g., "**B.8**")
2. Show the **full question text**
3. Say: "Answer out loud, then rate yourself: confident / shaky / blank"

Present **one at a time**. Wait for the user's self-rating before showing the next question.

**Do NOT provide the answer.** This is active recall, not a quiz with feedback. If the user explicitly asks "what's the answer?" or says they're stuck, then read the relevant source material and give a model answer.

### 4. Record Rating

After the user self-rates each question, update the state:

```json
{
  "last_drilled": "2026-02-21",
  "rating": "confident",
  "times_drilled": 3
}
```

Valid ratings: `confident`, `shaky`, `blank`

### 5. After Last Question

Update `sessions` count and `last_session` date in state. Save state file.

Show a brief summary:
```
Session 4 done. 2 confident, 1 shaky.
Shaky: B.8 (regulatory developments)
Next weak spot to revisit: F.30 (agentic frameworks)
```

If all 40 questions have been drilled at least once, congratulate and suggest reviewing the shaky/blank ones.

## Error Handling

- **If question bank file missing:** Tell user to check `~/code/vivesca-terry/chromatin/Capco/Capco Readiness Drill.md`
- **If state file corrupt:** Delete and recreate empty state
- **If user gives a rating not in (confident/shaky/blank):** Map synonyms — "good"/"solid"/"yes" → confident, "ok"/"partial"/"sort of" → shaky, "no"/"nothing"/"skip" → blank

---

## Mode: brief

Pull-based replacement for the daily cron. User pulls when they want it, not pushed daily.

### Workflow

1. **Run `date` first** — know the current date and days until Apr 8, 2026 start.

2. **Check First 30 Days checklist** — Read `~/code/vivesca-terry/chromatin/Capco/Capco - First 30 Days.md`. Identify one unchecked item that's actionable today. Prioritise "Must do" over "Should do" over "Nice to have".

3. **Search for fresh Capco content** — Web search for recent Capco publications on AI governance, financial crime, compliance technology. Filter to last 7 days. Also search HKMA + MAS + FCA for AI/fintech announcements.
   - If web search fails, output "No fresh signals retrieved" and continue with checklist + drill state only.

4. **Check drill weak spots** — Read `~/code/vivesca-terry/chromatin/Capco/.capco-drill-state.json`. If there are "blank" or "shaky" questions, suggest revisiting one.
   - If state file read fails, skip weak-spot suggestion.

5. **Output format** — concise, no fluff:

```
23 days to Capco.

📋 Action: [one specific thing from the checklist, with why it matters today]

📰 New this week:
- [article/announcement with 1-sentence summary and link, or "Nothing notable"]

🔄 Weak spot: [shaky/blank drill question to revisit, or "All drilled questions confident"]
```

**No canned talking points.** If there's a relevant article, link it and let the user form their own view.

---

## Mode: prep <event>

Meeting-specific preparation. The `<event>` is a free-text description like "coffee with Simon", "first day", "call with Tobin".

> **Consult [[career-communication]] reference doc** — pre-engagement prep, no blank asks, first impression window principles apply to all Capco/HSBC meetings.

### Workflow

1. **Identify the person(s)** from the event description.
   - If no person can be identified, ask one clarification question before proceeding.

2. **Check vault first** — Search `~/code/vivesca-terry/chromatin/Capco/` for existing prep notes (e.g., `Coffee Prep - Simon and Tobin.md`, `Bertie Haskins Profile.md`). Read any matches.
   - If no matches, continue with web search only.

3. **Web search for context** — Search LinkedIn and recent activity for each person. Search for any recent Capco publications they authored.
   - If web search fails, note "External context unavailable" and proceed with vault-only prep.

4. **Surface relevant drill questions** — Read the question bank. Pick 3-5 questions most relevant to this meeting's likely topics. E.g., coffee with Simon → A (tiering framework) + D (consulting delivery); call with Tobin → B (regulatory landscape).

5. **Check First 30 Days** — Any checklist items relevant to this meeting? (e.g., "Ask Gavin/Bertie for pre-reading" if meeting Gavin)

6. **Output format:**

```
Prep: Coffee with Simon Eltringham

👤 Context: [2-3 sentences on the person, role, what they care about]

📋 From your checklist:
- [relevant First 30 Days items, if any]

🎯 Drill questions to warm up on:
- A.1: 60-second pitch of the tiering framework
- D.20: "What does done look like in 8 weeks?"
- [etc.]

💡 Recent signals: [anything from web search worth knowing, or "Nothing new"]
```

**Don't script what to say.** Surface context and let the user prep naturally.

---

## Mode: status

Quick dashboard of drill progress.

### Workflow

1. Read `~/code/vivesca-terry/chromatin/Capco/.capco-drill-state.json` and `~/code/vivesca-terry/chromatin/Capco/Capco Readiness Drill.md`.

2. Output:

```
Drill progress: X/40 questions attempted, Y sessions

By category:
A. Tiering Framework: 3/7 drilled (2 confident, 1 shaky)
B. Regulatory: 1/7 drilled (1 blank)
[etc.]

⚠️ Never attempted: [list question numbers]
🔴 Blank: [list]
🟡 Shaky: [list]
```

---

## Notes (all modes)

- Keep it brisk. No lectures, no elaborate feedback.
- **Drill mode:** If the user says "rapid fire" — present all questions at once, user rates in batch. Self-rating is the point. Don't second-guess.
- **Brief mode:** No daily obligation. It's there when the user wants it.
- **Prep mode:** Vault notes are authoritative. Web search supplements, doesn't replace.
- This skill expires when Capco engagement starts (real work replaces practice). Delete after Day 1.

## Boundaries

- Do NOT draft outbound messages automatically; provide prep material only.
- Do NOT invent facts when vault/web context is missing; mark unavailable explicitly.
- Keep outputs concise and prep-oriented; no long-form essays.

## Example

> Prep: Coffee with Simon  
> Context from vault: AI governance, delivery shape, stakeholder mapping.  
> Checklist carry-in: confirm pre-reading and first-30-day priorities.  
> Warm-up drill: A.1, D.20, B.8.  
> Recent signals: none notable this week.
