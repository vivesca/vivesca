# AI Benchmark Data Access Reference (Feb 2026)

## Quick verdict table

| Source | API | Structured Data | Scrape-only | Update freq |
|---|---|---|---|---|
| Artificial Analysis | Yes (free key) | No download | No | Continuous |
| LM Arena | No | Conversation HF only; scores via community converter | Yes for live ELO | Continuous |
| SWE-bench (Princeton) | No | HF datasets + leaderboard JSON on GitHub | No | PR-driven |
| SWE-rebench (Nebius) | No | HF task corpus (not scores) | Partially | Monthly splits |
| LiveBench | No | HF: 6 category datasets + model_answer | No | Monthly |
| SEAL (Scale AI) | No | No (private by design) | Yes | Irregular |
| Aider | No | GitHub YAML files | No | Ad hoc (PR) |
| Terminal-Bench | No | HF: tasks + submission results | No | Ad hoc |

## 1. Artificial Analysis

- **API endpoint:** `GET https://artificialanalysis.ai/api/v2/data/llms/models`
- **Auth:** `x-api-key` header; free tier requires registration
- **Free limits:** 1,000 req/day
- **Media model endpoints:** `/api/v2/data/media/{text-to-image,image-editing,text-to-speech,text-to-video,image-to-video}`
- **Commercial tier:** Adds per-provider benchmarks, prompt-length breakdowns (contact required)
- **CritPt evaluate:** `POST /api/v2/critpt/evaluate` — 10 req/24h free
- **Sources:** https://artificialanalysis.ai/documentation, https://artificialanalysis.ai/api-access-preview

## 2. LM Arena (lmarena.ai)

- **Official API:** None for leaderboard scores
- **Conversation data:** `lmarena-ai/arena-human-preference-55k` on HuggingFace (55K battles, not scores)
- **Community ELO JSON:** https://github.com/nakasyou/lmarena-history — daily GitHub Actions update, parses pickle → `output/scores.json`
- **Community CSV scraper:** https://github.com/fboulnois/llm-leaderboard-csv — Python/R, parses HF Space app.py
- **Official export:** Requested feature, unimplemented as of July 2025
- **Methodology note:** The pickle→JSON conversion can break if lmarena changes internal format

## 3. SWE-bench (Princeton NLP, swebench.com)

- **Task datasets on HuggingFace:**
  - `princeton-nlp/SWE-bench` (2,294 tasks)
  - `SWE-bench/SWE-bench_Verified` (500 tasks, human verified)
  - `princeton-nlp/SWE-bench_Lite` (300 tasks)
  - `SWE-bench/SWE-bench_Multimodal`
- **Leaderboard scores:** Raw JSON at `data/leaderboards.json` in https://github.com/SWE-bench/swe-bench.github.io
- **No API**

## 4. SWE-rebench (Nebius, swe-rebench.com)

- **Task dataset:** `nebius/SWE-rebench-leaderboard` on HuggingFace — 1,390 rows, monthly splits (2025_01 through 2026_01), CC-BY-4.0
- **What it is NOT:** Not leaderboard scores — just task corpus
- **Leaderboard scores:** Displayed on swe-rebench.com dynamically; no structured download found
- **Rolling window:** 48 problems from rolling time window; scores shift over time

## 5. LiveBench (livebench.ai)

- **HuggingFace datasets (6 categories):**
  - `livebench/reasoning`, `livebench/math`, `livebench/coding`
  - `livebench/language`, `livebench/data_analysis`, `livebench/instruction_following`
  - `livebench/model_answer` (model responses: 93.7K rows, fields: question_id, model_id, choices, tstamp)
  - `livebench/model_judgment` (scores: 60.4K rows, fields: question_id, task, model, **score** [0-1], turn, tstamp, category)
- **Data format:** Parquet only (auto-converted from native format on HuggingFace)
- **JSON access:** No native JSON API. HF Datasets library can load parquet directly. No CSV export available on HF.
- **Python access (no parquet dependency):**
  - `from datasets import load_dataset; ds = load_dataset("livebench/model_judgment"); df = ds["leaderboard"].to_pandas()` → in-memory pandas (requires download + parquet parsing internally)
  - Alternative: fetch via HTTP + polars/arrow (still requires parquet library)
  - **No pure JSON/CSV alternative** without adding pyarrow/polars
- **Direct download:** `download_leaderboard.py` script in repo (outputs .jsonl question files + answer/judgment files)
- **Scoring structure:** Score per (model, question_id, task) tuple. Category score = avg task scores. Final score = avg category scores.
- **GitHub:** https://github.com/LiveBench/LiveBench (Apache 2.0, scoring code included)
- **Update frequency:** Monthly new questions; most recent fully public: Nov 2024; latest release: Apr 2025
- **No API**
- **Leaderboard:** https://livebench.ai/ (JavaScript-heavy, no JSON endpoint for live scores)

## 6. SEAL by Scale AI (scale.com/leaderboard)

- **API:** None
- **Dataset:** None — private eval data by design (anti-contamination)
- **Exception:** SWE-Bench Pro public task corpus at https://github.com/scaleapi/SWE-bench_Pro-os (731 tasks) — but no scores
- **Scrape-only:** Yes for all leaderboard scores
- **Update frequency:** Irregular; no published cadence

## 7. Aider (aider.chat/docs/leaderboards)

- **Data files:** YAML in GitHub repo: https://github.com/Aider-AI/aider/tree/main/aider/website/_data/
- **Key files:** `polyglot_leaderboard.yml`, `edit_leaderboard.yml`, `refactor_leaderboard.yml`, `qwen3_leaderboard.yml`
- **Raw access:** `https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/_data/<file>.yml`
- **Contributions:** PR-based; YAML format
- **No API**

## 8. Terminal-Bench (tbench.ai)

- **Task corpus:** `ia03/terminal-bench` on HuggingFace
- **Submission/results repo:** `sabhay/terminal-bench-2-leaderboard` on HuggingFace — official PR-based; stores per-agent result.json files
  - Structure: `submissions/terminal-bench/2.0/<agent>__<model>/<job>/result.json`
- **Verified results:** `zai-org/terminal-bench-2-verified`
- **GitHub:** https://github.com/laude-institute/terminal-bench
- **Submission:** Email mikeam@cs.stanford.edu or alex@laude.org; manual merge
- **Caveat:** HF dataset viewer was broken (DatasetGenerationError) at research time; raw files still accessible
- **No API**
