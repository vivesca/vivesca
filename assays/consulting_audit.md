# Consulting Readiness Audit

## Existing consulting modules
| Module | Functions | Status | Notes |
|--------|-----------|--------|-------|
| case_study.py | 8 (package_use_case, list_use_cases, _extract_section, _extract_metrics, _anonymise, CaseStudy.to_executive_summary, CaseStudy.to_car_arc, CaseStudy.to_slide_notes) | complete | Packages markdown use cases into exec summary, CAR arc, slide notes. Supports anonymisation. Reads from `Consulting/Use Cases/`. No create/store beyond file listing — relies on external markdown files existing. |
| talking_points.py | 6 (generate_talking_points, _scan_consulting_assets, _score_relevance, TalkingPoint.to_markdown, TalkingPointCard.to_markdown) | complete | Scans Consulting/Policies, Architectures, Use Cases, Experiments dirs. Scores relevance by client name + context keyword overlap. Generates structured talking point cards. Output is markdown only — no persistent storage of generated cards. |
| engagement_scope.py | 10 (scope_engagement, extract_timeline, extract_budget, extract_deliverables, extract_regulatory_context, extract_skills, detect_engagement_type, detect_risks, ScopeResult.to_markdown) | complete | Parses RFP/RFI text into structured scope with timeline, budget, deliverables, regulatory context, risk flags. Strong regex-based extractors. Covers HKMA, SFC, MAS, BIS, Basel, GDPR, DORA, etc. No persistence — returns dataclass only. |
| secretory_vesicle.py | 3 (secrete_text, secrete_image, _keychain) | complete (but not consulting-specific) | Telegram export channel. Sends text/images to Telegram. Not a consulting tool per se — it's the delivery pipe. Could be used to push deliverables to a consulting channel but has no consulting logic. |

## Existing consulting skills
| Skill | Trigger | Status |
|-------|---------|--------|
| expression | "weekly consulting IP production" | active — produces consulting IP (sparks → deliverables), LinkedIn seeds, Capco arsenal |
| metabolize | "process articles", "metabolize" | active — processes articles through Capco consulting lens, writes insight cards |
| opsonization | "meeting prep", "prep for meeting" | active — scenario-based drill for upcoming meetings/interviews |
| secretion | "package deliverable", "refine" | active — packages consulting artifacts for client delivery |
| chemoreception | "AI briefing on demand" | active — on-demand briefing refreshes context before meetings/decisions |
| adhesion | "evaluate this role", job URL | active — evaluates LinkedIn job postings for fit |
| phagocytosis | URL or pasted text | active — classifies content, extracts insights, saves as chromatin note |
| centrosome | "batch", "dispatch", "spec", "build" | active — spec writing + batch dispatch lifecycle (meta-skill for building) |
| endocytosis | "mine knowledge" | active — extracts tacit LLM knowledge into permanent reference skills |
| modification | "refine", "polish", "anneal" | active — multi-model artifact refinement |

**Note:** grep for 'consult|client|deliverable|engagement|meeting prep' in `~/.claude/skills/` returned 0 matches because triggers are in SKILL.md frontmatter, not raw keyword matches. All skills above are consulting-relevant by function.

## Knowledge base coverage
| Topic | Path | Status |
|-------|------|--------|
| AI Governance Consulting IP (110+ files) | `chromatin/Consulting/` | exists — extensive: engagement toolkits, regulatory scans, HSBC playbooks, Capco onboarding, vendor landscape, use cases, policies, architectures, experiments, templates |
| Capco-specific (60+ files) | `chromatin/Capco/` | exists — onboarding docs, day 1 strategy, 90-day scorecard, whitepaper summaries, conversation cards, qualifying questions, objection handlers, job descriptions |
| HSBC-specific (30+ files) | `chromatin/Consulting/` (HSBC-*) | exists — stakeholder maps, drill scenarios, engagement playbooks, DRA deep dives, peer benchmarks, acronym glossary, sandbox applications |
| Regulatory reference | `chromatin/euchromatin/regulatory/` | exists — 9 HKMA source docs parsed and stored |
| HKMA/SFC sweep | `chromatin/euchromatin/hkma-sfc-sweep/` | exists — regulatory pulse + summary |
| Consulting epistemics | `chromatin/euchromatin/consulting/` | exists — 28 files: governance frameworks, competitive landscape, maturity models, regulatory trackers |
| Consulting templates | `chromatin/Consulting/Templates/` | exists — meeting notes, RACI matrix, risk register, weekly status report (generic + HSBC-specific) |
| Consulting use cases | `chromatin/Consulting/Use Cases/` | exists — 8 banking AI use cases with index |
| Consulting architectures | `chromatin/Consulting/Architectures/` | exists — 6 agentic AI architecture references |
| Consulting policies | `chromatin/Consulting/Policies/` | exists — 10 policy templates (AUP, incident response, board reporting, etc.) |
| Consulting experiments | `chromatin/Consulting/Experiments/` | exists — context window governance, prompt injection red team |
| Chemosensory cards | `chromatin/chemosensory/cards/` | exists — 3 recent daily intelligence cards |
| Client research pipeline | — | missing — no automated client/competitor research pipeline |
| Time tracking / timesheets | — | missing |
| Expense tracking | — | missing |
| Deliverable versioning | — | missing — no git-based or structured version tracking for client deliverables |
| Client CRM / relationship map | `chromatin/Capco/Key People.md`, `capco-networking-map` | partial — static files, no structured CRM |
| Engagement financials (utilization, billing) | — | missing |
| SOW/contract templates | `chromatin/Capco/Consulting SOW Proposal Guide.md` | exists — guide but not automated template generation |
| Capco internal methodology | `chromatin/Capco/Capco Methodology Brief - 2026-03.md` | exists |

## Gaps (prioritized for Capco Day 1)
| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| **Client research automation** — auto-gather news, filings, org changes for named clients (HSBC initially) | high | medium | P1 |
| **Meeting prep → debrief pipeline** — opsonization drills but no structured capture of what happened in meetings, action items, follow-ups | high | small | P1 |
| **Weekly status report generator** — templates exist but no automation to populate from calendar + task data | high | small | P1 |
| **Deliverable tracker** — no tracking of what's been delivered, what's pending, versions, client sign-offs | high | medium | P2 |
| **Time/effort logging** — no timesheet or utilization tracking | medium | medium | P2 |
| **Friday note / stakeholder update automation** — template exists but no auto-population from week's work | high | small | P2 |
| **Capco vocabulary / jargon drill** — flashcards existed but may be stale; no spaced repetition integration | medium | small | P2 |
| **Engagement risk register** — engagement_scope.py detects risks but no persistent risk register tracking | medium | small | P2 |
| **Cross-client pattern library** — talking_points.py scans one Consulting dir; no multi-client pattern extraction | medium | large | P3 |
| **Conference / thought leadership pipeline** — abstracts drafted but no submission tracking or deadline management | medium | small | P3 |
| **Expense / receipt capture** | low | medium | P3 |
| **Knowledge decay monitoring** — no staleness detection on consulting IP (many files dated Mar 2026, may age quickly) | medium | small | P3 |

## Summary
- Consulting modules: 4 (3 complete, 1 complete but not consulting-specific)
- Consulting skills: 10 (all active)
- Knowledge topics covered: 14 (13 existing, 1 partial)
- P1 gaps: 3
- P2 gaps: 4
- P3 gaps: 4

## Observations

**Strong foundations.** The consulting infrastructure is unusually mature for a pre-Day-1 consultant. The `expression` skill runs weekly IP production. `metabolize` processes articles through a Capco lens. `opsonization` handles meeting prep. `secretion` packages deliverables. The knowledge base has 200+ consulting-relevant files spanning HSBC intelligence, regulatory references, Capco onboarding, and consulting IP.

**Key strength: knowledge density.** The `chromatin/Consulting/` vault alone has 110+ files covering engagement toolkits, use cases, policies, architectures, and regulatory scans. The `chromatin/Capco/` directory has 60+ files. This is a ready-made consulting brain.

**Key weakness: the loop isn't closed.** Skills generate content (talking points, scope, case studies) but don't persist structured outputs. Modules return dataclasses but don't write back. There's no feedback loop from meeting outcomes back into the knowledge base. The system is rich on preparation but thin on capture.

**Recommended first actions (Week 1):**
1. Build a `meeting_debrief` function in engagement_scope.py or a new organelle that captures post-meeting notes, action items, and follow-ups into a structured format
2. Wire the existing weekly status report template to auto-populate from calendar + circadian data
3. Add a client research cron that runs `rheotaxis_search` for HSBC news weekly and deposits into `Consulting/`
