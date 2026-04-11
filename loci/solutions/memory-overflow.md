# Memory Overflow

Demoted from MEMORY.md for budget. Search when a topic needs looking up.


## 2026-04-10 — demoted sections

## Dispatch
- [Epigenome syncs to ganglion](finding_ribosome_epigenome_invisible.md) — cron pull every 5min; ribosome can read ~/epigenome/ directly now
- [Manifest mode](finding_manifest_mode_design.md) — FILE/END_FILE/RUN/FIX_IF_FAILING format for zero-token file creation, LLM only for fixes
- [GLM imperative preamble](finding_glm_imperative_preamble.md) — large specs need "You are an executor. CREATE THE FILES." prefix or GLM treats as document
- [Codex not on ganglion](finding_codex_not_on_ganglion.md) — `--provider codex` fails exit=127; doctor checks key not binary
- [Dispatch boldly](feedback_dispatch_boldly.md) — don't deliberate dispatch risk; re-dispatch is free
- [Ribosome harness benchmark](finding_ribosome_harness_benchmark.md) — CC+Max ~1min, Goose+ZhiPu ~2min (free). Creds portable via scp.
- [ZhiPu CC config](reference_zhipu_coding_plan_cc_config.md) — `ANTHROPIC_AUTH_TOKEN` (not API_KEY!), `/api/anthropic` endpoint, `hasCompletedOnboarding`, GLM-5.1 model mapping. Ribosome was using wrong env var.
- [CC --print finding](finding_cc_print_mode_cripples_ribosome.md) — CC on ganglion failed because of wrong auth env var + missing onboarding bypass, not because of --print mode or ZhiPu slowness.
- [Distribution test vs demand](feedback_evaluate_distribution_against_demand.md) — test 1 evaluates generalized potential, not current coupling
- [Volcano hallucination](finding_volcano_hallucination.md) — doubao claims "done" without writing code. Don't use for build tasks. NOTE: mtor Apr-8 batch was NOT hallucination — commits existed on main, diff capture failed (see verdict false positive finding).
- [Review gate repo blindness](finding_review_gate_repo_blindness.md) — translocase hardcoded to germline, tasks targeting ~/code/* falsely rejected. Fixed in eb154998.
- [No cherry-pick, use origin](feedback_no_cherry_pick_use_origin.md) — push to GitHub origin, pull on other machine. Cherry-picks create divergent histories. **Protected.**
- [mtor three failure modes](finding_mtor_three_failure_modes.md) — empty-diff stall blindness, cancel doesn't kill subprocess, no dispatch dedup. 3 specs in `loci/plans/`.
- [Verdict false positive from concurrency](finding_verdict_false_positive_concurrency.md) — `no_commit_on_success` fires falsely under concurrent git access. HEAD-moved fallback patched 2026-04-08. **Protected.**


## Research
- [mtor/ribosome landscape](finding_mtor_ribosome_landscape.md) — architect-implementer AI coding systems survey, steal list, distribution test result
- [mtor package status](project_mtor_status.md) — v0.7.0, 434 tests, worker on ganglion from ~/code/mtor (migrated from polysome 2026-04-08). Concurrency 2/provider.
- [OpenCode harness eval](finding_opencode_kilo_harness_evaluation.md) — 12-task×4-harness benchmark done. OpenCode added to ribosome. Correctness = model, not harness. Route by task type.
- [CLI framework: cyclopts + porin](finding_cli_framework_cyclopts.md) — standard stack for all distributable CLIs; cyclopts>=4.0, porin>=0.3
- [epsin scraper CLI](project_epsin_status.md) — v0.1.0 on PyPI, 23 sources, extractor plugins, cyclopts+porin
- [Karpathy LLM Wiki steals](finding_karpathy_llm_wiki_steals.md) — 9 patterns stolen (supersedes, confirmed, action fields; TreeSearch; type ordering; file-back). Sources traced.
- [Harness encodes expiring assumptions](finding_harness_encodes_expiring_assumptions.md) — coaching files compensate for model limits that expire. Test and prune, don't just accumulate. From Anthropic Managed Agents.

