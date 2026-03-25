# GARP Portal Navigation — Operational Reference

## Access

- **Login URL:** https://garp.my.site.com/
- **Credentials:** `adytum get garp` or 1Password export (terry.li.hm@gmail.com)
- **Learning platform:** https://garplearning.benchprep.com/app/rai26 (SSO via GARP portal — click "2026 GARP Learning RAI" → Access)

## agent-browser Login Flow

The GARP portal login form uses non-standard field names. Standard `agent-browser auth login` fails. Manual field approach:

```bash
agent-browser open "https://garp.my.site.com/"
agent-browser wait 2000
agent-browser type "input[name='j_id0:j_id9:username']" "terry.li.hm@gmail.com"
agent-browser type "input[name='j_id0:j_id9:password']" "<password>"
agent-browser click ".login-btn"
agent-browser wait 3000
# Should land at https://garp.my.site.com/garpapp#/dashboard
```

Then navigate to learning platform:

```bash
agent-browser open "https://garp.my.site.com/garpapp#/study-materials"
agent-browser wait 3000
agent-browser click "button:has-text('Access')"   # opens GARP Learning RAI modal
agent-browser wait 3000
agent-browser click "button:has-text('Access')"   # clicks Access inside modal
agent-browser wait 5000
# Should land at https://garplearning.benchprep.com/app/rai26
```

## Learning Platform Structure (benchprep)

- **Home:** Module-level Strengths & Weaknesses overview
- **Study Plan:** Full structured chapter list with progress tracking
- **Lessons → Table of Contents:** Full TOC; "Expand All" button works but nav link clicks time out — use `#read/table-of-contents` URL directly
- **Practice Exam:** 40Q full practice exam

### Key URLs

```
Home:          https://garplearning.benchprep.com/app/rai26
Study Plan:    https://garplearning.benchprep.com/app/rai26#study-plan
TOC:           https://garplearning.benchprep.com/app/rai26#read/table-of-contents
M3 content:    https://garplearning.benchprep.com/app/rai26#read/section/risk-and-risk-factors-questions
```

### Gotchas

- `agent-browser click "link[ref=eXX]"` times out on nav links — use `agent-browser open <url>` with hash fragments instead
- TOC expand buttons also time out on click — read text content directly instead
- `agent-browser get text body` + grep is the most reliable way to extract structured content
- M3/M4/M5 don't expand sub-sections in the TOC UI — navigate directly to section URLs

## Curriculum Structure (RAI 2026)

5 core modules + 1 optional supplementary:

| Module | Title | Sub-structure |
|--------|-------|--------------|
| M1 | AI and Risk — Introduction and Overview | 3 sections (Classical AI, Neural Nets, ML Risks) + nav intro |
| M2 | Tools & Techniques | 10 chapters (Ch1-Ch10), each with numbered sub-sections |
| M3 | Risk and Risk Factors | Single chapter, 9 sections (2–9) |
| M4 | Responsible & Ethical AI | Single chapter |
| M5 | Data and AI Model Governance | Single chapter |
| M6 | Supplementary (Optional) | Case studies, articles, webcasts, papers — NOT examinable |

## Scrape Lessons Learned (Mar 2026)

**LRN-20260310-001: Benchprep shows condensed content, not full textbook**
The original M2 file had 37,000+ lines from what appears to be the full printed textbook. The benchprep online platform only serves condensed lesson pages (~11k lines for M2). These are different sources. A re-scrape via agent-browser will always produce the condensed version. If full textbook depth is needed, the original source was NOT benchprep — unknown where it came from (possibly a manual PDF extraction or an earlier platform version). **Never overwrite M2 with a benchprep scrape** — it will always be a regression.

**LRN-20260310-002: Keyword/size checks pass even on regressions — diff is the critical gate**
M2 passed all keyword and size checks (86k words > 50k minimum) despite losing 36k lines of content. Only the diff caught the regression. For any future scrape: run diff first, keyword checks second. A module that "passes" but shows massive line loss in diff = bad scrape regardless of keyword presence.

**LRN-20260310-003: Boundary sections are misclassification risks**
"Responsible Governance of GenAI" is a M5 topic but contains keywords matching M4 (ethics, governance). Agent scraper classified it into M4. Any section that conceptually spans modules (e.g. GenAI risk in M3, GenAI governance in M5) needs explicit module assignment rules, not just keyword matching.

## Scrape Verification Script

After any re-scrape, run:
```bash
# First back up old files
mkdir -p ~/tmp/garp-backup
for n in 1 2 3 4 5; do cp "/Users/terry/notes/GARP RAI Module $n - Raw Content.md" "~/tmp/garp-backup/m${n}-old.md"; done

# Then verify new files
uv run --script ~/bin/verify-garp-scrape.py
```

Checks: word count minimums, 15-18 key concepts per module, expected section headings, and diff vs old files (regressions = lost content = bad). Script: `~/bin/verify-garp-scrape.py`.

## Raw Content Completeness Verification (Mar 2026)

All 5 modules confirmed complete against portal:
- M1: 3 core sections present ✅
- M2: All 10 chapters with all sub-sections ✅
- M3: All 9 sections present; scrape checklist all `[x]` ✅
- M4/M5: Structure matches portal (single chapters) ✅
- M6: Not scraped — supplementary only, not needed ✅

**Minor discrepancy:** Portal shows "8.2 Global Inequality" as a sub-heading in M3; raw content covers the same material under 8.0 without the sub-heading. Content complete, heading granularity differs.

## Study Guide PDF

Official Study Guide & Learning Objectives (Dec 1, 2025 version) available at:
`https://www.garp.org/landing/rai-study-guide-and-learning-objectives` (form-gated)

Contains: per-chapter question counts, full LO list, exam weighting per module.
