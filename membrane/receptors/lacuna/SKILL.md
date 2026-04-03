---
name: lacuna
description: Demo CLI for Lacuna regulatory gap analysis platform. Use when working on Lacuna demos, Railway deployment, or CLI wrapper tasks.
user_invocable: false
triggers:
  - lacuna
  - demo
  - railway
  - gap analysis
  - regulatory
  - compliance
  - preflight
  - warmup
---

# lacuna

Demo CLI for Lacuna regulatory gap analysis. Wraps the Railway API with Rich output.

**Script:** `~/bin/lacuna` (uv run --script, no install needed)
**API:** `https://lacuna.sh` (custom domain) — Railway: `https://lacuna-production-8dbb.up.railway.app`
**Auth:** set `LACUNA_API_KEY=<key>` env var — CLI auto-injects `X-API-Key` header on all requests.

## Commands

```bash
lacuna docs                                          # list all documents (9 live; NIST/SG PDFs not in repo)
lacuna preflight                                     # health check: API + docs + cache (use before demo)
lacuna chat                                          # interactive chat with full corpus
lacuna chat --jurisdiction hk                        # chat filtered to HK docs
lacuna gap --circular hkma-cp --baseline demo-baseline           # run gap analysis
lacuna gap --circular hkma-cp --baseline demo-baseline --verbose # with reasoning + citations
lacuna query "What are HKMA's GenAI consumer protection requirements?" --jurisdiction hk
lacuna warmup                                        # pre-warm Railway cache before demo

# Upload
lacuna upload path/to/doc.pdf --name "My Policy Doc"  # upload document (LLM extraction)
lacuna upload path/to/doc.txt --name "My Policy Doc" --no-llm  # upload without LLM (chunks only)

# Multi-gap (batch)
lacuna multi-gap --circular hkma-cp --baselines demo-baseline nist-rmf  # compare circular vs multiple baselines

# Export
lacuna export --circular hkma-cp --baseline demo-baseline --format pdf   # download PDF report
lacuna export --circular hkma-cp --baseline demo-baseline --format docx  # download Word report
lacuna export --circular hkma-cp --baseline demo-baseline --format md    # markdown summary

# Annotation / remediation tracking
lacuna annotate --req-id <circular_req_id> --status addressed --owner "Compliance" --notes "Covered in §4.2"
lacuna annotate --req-id <id> --status in-progress   # status: open | in-progress | addressed | not-applicable
lacuna remediate --circular hkma-cp --baseline demo-baseline  # Rich table: gap + review status + owner + %
```

## Doc Aliases

| Alias | Document |
|-------|----------|
| `hkma-cp` | HKMA GenAI Consumer Protection 2024 |
| `hkma-gai` | HKMA GenAI Financial Services 2024 |
| `hkma-sandbox` | HKMA GenAI Sandbox Arrangement 2024 |
| `hkma-spm` | HKMA SPM CA-G-1 Revised 2024 |
| `eu-ai-act` | EU AI Act (Regulation 2024/1689) |
| `fca` | FCA AI Update 2024 |
| `mas-consult` | MAS AI Risk Management Consultation 2025 |
| `mas-mrmf` | MAS AI Model Risk Management 2024 |
| `demo-baseline` | Codex Argentum v1.1 (Capco-authored illustrative baseline) |
| `nist-rmf` | NIST AI Risk Management Framework 1.0 |
| `nist-iso42001` | NIST AI RMF → ISO 42001 Crosswalk |
| `sg-genai` | Singapore GenAI Governance Framework 2024 |

Raw UUIDs also accepted anywhere an alias is used.

## Demo Day Checklist

**Night before:**
1. `lacuna preflight` — full health check (API + 12 docs + cache warmup in one command)
2. Expected: `PASS — demo ready.` with Full:0 Partial:6 Gap:2 (hkma-cp vs Codex Argentum v1.1, Mar 6 re-seed) — always re-verify, counts shift after re-seeds
3. Start a QuickTime screen recording as backup before the meeting

**Day of (before Tobin arrives):**
1. `lacuna preflight` again — cache resets on Railway restart
2. Have these queries ready to paste:
   - `What are HKMA's requirements for GenAI consumer protection?`
   - `What are the high-risk AI system requirements under the EU AI Act?`
3. Bring a 5G mobile hotspot — office wifi may block Railway/Railway egress

**If preflight shows FAIL:**
- API unreachable → check network, try `LACUNA_API_URL=http://localhost:8000 lacuna docs` for local fallback
- Missing docs → Railway restarted and volume still mounting; wait 60s and retry
- Cache warm failed → run `lacuna warmup` manually; first run can take 30s+

## Gotchas

- **`is_policy_baseline` is always `false`** — all docs are in doc_repo, not policy_repo. The script hardcodes this; don't change it.
- **Gap analysis timeout is 45s** — if Railway cold-started, first run can exceed this. Always warmup.
- **Cache is in-memory on Railway** — resets on every service restart. Re-run `lacuna warmup` (or `lacuna preflight`) if Railway was redeployed.
- **NIST, NIST crosswalk, and demo-baseline show jurisdiction "-"** — hardcoded in BASELINES set; they're not jurisdiction-specific.
- **Gap analysis on no_llm baselines works — quality is demo-grade.** Tested: `lacuna gap --circular hkma-cp --baseline fca` (FCA is no_llm) produced coherent Full/Partial/Gap with chunk citations. The system already falls back to chunk-based reasoning when requirements are empty. "Sparse" note in older docs was overly conservative.
- **Upload is 5+ min even with --no-llm.** Bottleneck is sentence-transformer embedding generation on Railway CPU, not LLM extraction. Live upload during a meeting is not viable. Strategy: pre-upload the night before, or use an already-ingested doc (mas-mrmf) as the credibility test.
- **sg-genai and nist-iso42001 uploaded no_llm** — chunks exist for RAG queries. Gap analysis works. All 12 docs now in system after Mar 6 re-seed (PDFs were in `data/documents/corpus/` after all).
- **Override API URL:** `LACUNA_API_URL=http://localhost:8000 lacuna docs` for local dev.
- **uv resolves deps on first run** — if demo machine has never run it, first invocation hits PyPI (needs internet). Pre-warm by running any lacuna command once the day before.
- **Auth is bypass-enabled when LACUNA_API_KEYS not set on server** — dev/local mode works without key. Set before production deploy.
- **`lacuna remediate` returns 404** if `/remediation/plan` endpoint not yet deployed — prints graceful message, not a crash.
- **`lacuna upload` has 600s timeout** — LLM extraction takes 2-3 min; Railway's HTTP timeout is tight for large docs (hkma-gai took 369s). Use `--no-llm` for very large docs.
- **Volume is now persistent** (`lacuna-volume` at `/app/data`). If data is ever lost: `cd ~/code/lacuna && python3 tools/seed_corpus.py && python3 tools/update_aliases.py`. Source PDFs in `data/documents/corpus/`.
- **NIST/SG docs ARE in repo** (`data/documents/corpus/global/`, `data/documents/corpus/sg/`) — uploaded no_llm. Previously thought missing; confirmed present after Mar 6 re-seed.
- **Dockerfile: `libgdk-pixbuf-2.0-0` not `libgdk-pixbuf2.0-0`** — Debian Bookworm renamed the package. Old name breaks `apt-get install` silently across all builds.
- **Railway build failures → read the build log URL** printed by `railway up`, or run `railway logs --build <deployment_id>`. Don't diagnose from local Docker — silent `apt-get` failures and import errors are only visible in Railway's build log. See `~/docs/solutions/railway.md` for full reference.
- **Frontend fetch wrapper patches `window.fetch` globally** — all XHR calls auto-inject `X-API-Key` from localStorage. Export PDF/DOCX buttons use fetch+blob (not window.open), so auth is always included.

## Second Credibility Baseline

For the "I didn't write this doc" credibility test during demo:
```bash
lacuna gap --circular hkma-cp --baseline nist-rmf
```
NIST AI RMF was uploaded `no_llm=true` so findings will differ from the primary pair.

## Files

- Script: `~/bin/lacuna`
- Vault: `~/notes/Capco/Lacuna/` (symlinks to CLAUDE.md, DEMO_SCRIPT.md, Codex Argentum)
- **Product strategy** (CLI-first principle, completeness workflow design): `~/notes/Capco/Lacuna/Lacuna - Product Strategy.md`
