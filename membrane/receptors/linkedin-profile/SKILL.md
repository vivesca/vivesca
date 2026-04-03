---
name: linkedin-profile
description: Manage Terry's LinkedIn profile — Featured links, About section, headline, announcements, job updates. NOT for researching other people.
triggers:
  - update my LinkedIn
  - add to LinkedIn profile
  - LinkedIn announcement
  - LinkedIn about section
  - featured link
---

# linkedin-profile — Own Profile Management

## Profile URL
https://www.linkedin.com/in/terrylihm/

## Access
LinkedIn blocks WebFetch (HTTP 999). Use agent-browser with Chrome cookies:
```bash
porta inject --browser chrome --domain linkedin.com
agent-browser open https://www.linkedin.com/in/terrylihm/
agent-browser wait 4000
agent-browser snapshot
```

## Key Sections to Update

### Featured (most visible — custom links with description)
- Add links to tools, posts, projects with title + description
- Current: terryli.hm, consilium.sh
- Edit: Profile → Featured → Add → Link

### About
- Long-form bio. Terry's voice, not performative.
- Current framing: AGM/Head of DS at CNCBI → Capco Principal Consultant, AI Solution Lead
- Key credentials to mention: HKMA GenAI Sandbox (1 of 10 banks), FCPA, CIA
- End with pointer to terryli.hm for public writing

### Headline
- Current: check via snapshot before editing
- Format: Role @ Company · one-line differentiator

### Announcements (new role, milestone)
- Draft via `message` skill for tone
- Hold until start date confirmed (Capco)
- See [[Capco Transition]] for timing gate

## Adding a Featured Link
1. Open profile via agent-browser
2. Scroll to Featured section → click + → Add link
3. Fields: URL, title (≤58 chars), description (≤200 chars)

## terryli.hm Featured Entry
- URL: https://terryli.hm
- Title: terryli.hm — Working Notes
- Description: Where I think in public. Production AI in financial services, agentic systems, and what it means to build alongside machines. Posts get revised as thinking develops.

## Gotchas
- LinkedIn blocks `networkidle` wait — use `wait 4000` fixed ms
- Notification onboarding loop: `close` → `porta inject` → `open` → `wait 4000`
- Draft announcements; never send directly — pause before posting
- Profile edits are live immediately, no staging
