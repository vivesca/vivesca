---
name: opsonization
description: Drill for upcoming meetings or interviews with scenario practice. "meeting prep"
user_invocable: true
triggers:
  - meeting prep
  - prep for meeting
  - prep for coffee
  - prep for interview
  - opsonization
epistemics: [negotiate, communicate]
---

# Meeting Prep

Scenario-based drill for upcoming meetings. Generates likely questions, objection scenarios, and knowledge checks — then coaches on the strongest response framing.

## Trigger

- "meeting prep", "prep for meeting", "prep for coffee", "prep for interview"
- `/opsonization` or `/opsonization 5`

## Inputs

- **meeting** (required first time): Meeting context — who, what, stakes. Can reference a chromatin note (e.g., "Simon/Tobin coffee") or be free text.
- **count** (optional): Number of questions. Default 5.
- **mode** (optional): `questions` (likely Qs you'll face), `objections` (pushback scenarios), `knowledge` (domain knowledge checks). Default: `questions`.

> **Consult [[career-communication]] reference doc** for pre-engagement prep principles — research-first, specific observations, first impression window.
> **see [[mental-models]]** — scan for applicable models (incentives, principal-agent, circle of competence) to frame stakeholder reasoning.

## Workflow

### 1. Gather Context

If the user provides a meeting description, use it directly. If they reference a note or person, read the relevant chromatin files:

- `~/epigenome/chromatin/MOC - Capco & HSBC Engagement.md` — if Capco/HSBC-related
- `~/epigenome/chromatin/Job Hunting.md` — CV narrative, comp, story framing
- `~/epigenome/chromatin/Interview Q&A Bank.md` — prepared answers for common questions
- `~/epigenome/chromatin/Core Story Bank.md` — STAR-format behavioral stories
- `~/epigenome/chromatin/Praxis.md` — for meeting-specific context and deadlines
- Any person-specific or company-specific notes the user mentions

Also read these for Terry's personal background and career context:
- `~/epigenome/chromatin/Capco/Capco Transition.md` — current role, transition context, Capco engagement
- `~/epigenome/chromatin/CNCBI Project Facts.md` — CNCBI project history, achievements, key facts
- `~/epigenome/chromatin/Core Story Bank.md` — STAR-format behavioral stories for behavioral questions

### 2. Generate Question

Generate ONE scenario-based question grounded in the meeting context.

**By mode:**

- **questions**: What will the other person likely ask? (e.g., "Tell me about your AI governance experience", "What's your view on LLM risk in banking?")
- **objections**: Pushback scenarios (e.g., "Client says the timeline is too aggressive — how do you respond?", "Stakeholder questions why you need a dedicated data science team")
- **knowledge**: Domain knowledge you should have ready (e.g., "What did the HKMA's GenAI sandbox programme involve?", "Name three key requirements of the EU AI Act")

**Format as MCQ (A-D):**

- One option is the strongest/most strategic response
- Three distractors are plausible but suboptimal:
  - Too aggressive or defensive
  - Too vague or too detailed
  - Technically correct but politically naive
  - Misses the strategic angle or rapport opportunity

**Question variety** — rotate through these stems across a session:

- Direct question: "They ask you: ..."
- Scenario: "During the meeting, [person] says: ..."
- Curveball: "Unexpectedly, the conversation shifts to ..."
- Rapport test: "There's a lull. How do you steer the conversation toward ..."

### 3. Present via AskUserQuestion

Use `AskUserQuestion` with:
- `header`: "Q{n}"
- `question`: The full scenario/question
- Options A-D as `options` (label = answer text, description = brief qualifier if needed)
- `multiSelect`: false

### 4. Evaluate & Coach

After the user answers:

- State whether their choice was the **strongest option** (not "correct" — this is coaching, not testing)
- Explain **why** the best answer works: framing, tone, strategic positioning
- If suboptimal, name the **specific risk**: comes across as defensive, misses the power dynamic, over-shares, etc.
- Suggest a **concrete phrasing** (1-2 sentences) they could actually say in the meeting
- Where relevant, reference their actual experience from the Story Bank or CV

**Coaching tone:** Direct, not patronizing. Think executive coach, not schoolteacher.

### 5. Loop or Finish

- Continue until count reached
- After last question, show session summary:
  - Score (e.g., "4/5 strongest picks")
  - **Key talking points** — the 3-5 best framings from the session, written as bullet points they can review before the meeting
  - Flag any blind spots or areas to think more about

### 6. Save Prep Notes (optional)

Ask if they want to save. If yes, save to `~/epigenome/chromatin/Meeting Prep - [Context].md` with:
- Meeting context header
- Key talking points (best framings from session)
- Any flagged blind spots
- Date of prep session

## Error Handling

- **If no meeting context given**: Ask via AskUserQuestion — "Which meeting are you prepping for?" with recent upcoming meetings from Praxis.md as options
- **If referenced note doesn't exist**: Fall back to user's description + background from `~/epigenome/chromatin/Capco/Capco Transition.md` and `~/epigenome/chromatin/CNCBI Project Facts.md`
- **If user wants to stop mid-session**: Show partial summary with talking points so far

## Output

- Questions presented via `AskUserQuestion` (interactive MCQ UI)
- Coaching feedback in chat after each answer
- Session summary with key talking points at end
- Optional: prep notes saved to chromatin

## Notes

- This is **coaching**, not testing — the "best" answer is about strategic effectiveness, not factual correctness
- Keep explanations actionable: "Say X instead of Y because Z"
- Reference Terry's actual experience (AML model, GenAI sandbox, agent-assist chatbot, team building) in suggested framings
- For senior stakeholders: emphasize political awareness, strategic framing, knowing when to hold back
- For interviews: test STAR conciseness and confident-but-not-arrogant tone
- For networking/coffee: test rapport-building and ask-vs-tell balance
- Don't repeat the same scenario type within a session
- Weight toward the hardest questions — easy rapport Qs don't need drilling
