---
name: libra
description: Run and manage the Libra AI use case tier classifier. Use when demoing to Simon, updating tiering rules, or running locally.
---

# Libra — AI Use Case Tier Classifier

HSBC AI Risk Tiering Framework as a self-service web app. Built for Simon Eltringham (Responsible AI Governance Manager, HSBC).

## Run locally

```bash
cd ~/code/libra && pnpm dev
# → http://localhost:3000
```

## What it does

- User enters a use case name + description
- Scores 5 dimensions (Decision Impact, Model Complexity, Data Sensitivity, Autonomy, Regulatory Exposure) — each 1-3
- Checks override flags (9 auto-escalation triggers, 3 de-escalation conditions)
- Outputs: Tier 1/2/3, composite score, governance path, required artifact checklist, Markdown copy button

## Key files

| File | Purpose |
|------|---------|
| `lib/tiering-engine.ts` | Pure scoring + override logic. No React. Fully tested. |
| `config/tiering.ts` | All dimension criteria, tier thresholds, artifact lists, governance paths |
| `types/index.ts` | Shared TypeScript types |
| `components/DimensionForm.tsx` | 5-dimension form with accordion scoring cards |
| `components/ResultsView.tsx` | Tier badge, score bars, checklist, copy button |
| `app/page.tsx` | Wires form → engine → results |

## Updating tiering rules

The framework logic lives in **`config/tiering.ts`** — not in the engine. To update:
- Dimension criteria/examples → `DIMENSION_CRITERIA`
- Tier thresholds (score ranges) → `TIER_THRESHOLDS`
- Required artifacts per tier → `REQUIRED_ARTIFACTS`
- Governance path text → `GOVERNANCE_PATHS`
- Override rule labels → `OVERRIDE_ESCALATION_LABELS` / `OVERRIDE_DEESCALATION_LABELS`

The engine (`lib/tiering-engine.ts`) reads from config — no logic changes needed for rule updates.

## Tests

```bash
cd ~/code/libra && pnpm test
```

8 tests covering: Tier 3/2/1 assignment, escalation override, de-escalation, escalation-beats-de-escalation priority, artifact lists, summary text.

## Demo script for Simon

1. Open `http://localhost:3000`
2. Say: "Give me one of your queued use cases"
3. Fill it in together — let Simon answer the dimension questions
4. Watch the override flags section — if it's a vendor API, check `materialOutsourcing` and watch it jump to Tier 1
5. Hit "Copy Summary" → paste into Confluence/email

## Gotchas

- **Tailwind v4** (not v3) — uses `@import "tailwindcss"` syntax, not `@tailwind` directives. Don't revert.
- **Next.js 16** — not 14 as originally planned. No functional difference.
- **vitest needs `@/*` alias** — already set in `vitest.config.ts`. If you add new test files importing from `@/`, it works.
- **No backend/DB** — fully stateless. No deployment config needed. `vercel --prod` from repo root deploys immediately if needed.

## Deploy to Vercel (if Simon wants a URL)

```bash
cd ~/code/libra && pnpm build && vercel --prod
```
