# Golem Task Queue

Tasks waiting for dispatch. CC adds, golem consumes. Keep ~10 tasks ahead.

## Pending

### Infrastructure
- [ ] `golem --max-turns 30 "Build effectors/golem-daemon as Python. Reads ~/germline/loci/golem-queue.md for '- [ ]' lines with golem commands in backticks. Runs up to 4 concurrent golem subprocesses. When one finishes, marks line '- [x]' and starts next. Polls every 30s. Subcommands: start (nohup), stop (pidfile kill), status. Pidfile ~/.local/share/vivesca/golem-daemon.pid. Log to ~/.local/share/vivesca/golem-daemon.log. Test: golem-daemon status"`
- [ ] `golem --max-turns 30 "Build effectors/council as Python. Takes a position/decision as argument. Dispatches codex exec and gemini -p in parallel with 'Challenge this: <position>. What's wrong? What was missed? Strongest argument against? 200 words max.' Collects both responses, outputs structured report: convergence points, divergence points, risks flagged. Usage: council 'We should refactor X into Y'. Test it."`
- [ ] `golem --max-turns 30 "Add --provider flag to effectors/golem. Providers: zhipu (default), bailian, minimax, infini. Each sets different ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, and model env vars. Read ~/epigenome/chromatin/Reference/coding-plan-comparison-2026.md for endpoints. API keys from env vars: ZHIPU_API_KEY, BAILIAN_API_KEY, MINIMAX_API_KEY, INFINI_API_KEY. Test: golem --provider bailian 'echo hello'"`
- [ ] `golem "Build effectors/browse as Python. Reliable web content extractor with fallback chain: 1) defuddle parse URL --md, 2) if empty curl + html2text, 3) if still empty print NEEDS_BROWSER. Usage: browse URL. Output clean markdown to stdout. Test with 3 URLs."`

### Features
- [ ] `golem --max-turns 30 "Read metabolon/organelles/engagement_scope.py. Add debrief() function: takes meeting_notes str, attendees list, date str. Extracts action items, decisions, discussion points. Returns structured dict. Write tests. Run pytest. Fix failures."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/complement.py. Add coverage_summary() function: cross-refs metabolon/ modules against assays/ test files. Returns {tested, untested, coverage_pct, untested_modules}. Write tests. Run pytest. Fix failures."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/talking_points.py. Add weekly_refresh function. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/case_study.py. Add generate_from_template with CAR framework. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/sortase/validator.py. Add check_test_coverage validation. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/translocon.py. Add dispatch_stats function. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/metabolism/preflight.py. Add check_golem_ready. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/glycolysis_rate.py. Add suggest_conversions. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/chromatin.py. Add stale_marks and type_counts methods. Write tests. Run pytest."`
- [ ] `golem "Create effectors/capco-prep — reads chromatin/Capco/, lists docs, flags stale, outputs readiness checklist"`
- [ ] `golem "Create effectors/weekly-status — git stats, test count, calendar, outputs markdown report"`

### Tests (remaining untested modules)
- [ ] `golem --max-turns 40 --batch metabolon/pore.py metabolon/pulse.py metabolon/organelles/statolith.py`
- [ ] `golem --batch metabolon/respirometry/parsers/boc.py metabolon/respirometry/parsers/hsbc.py metabolon/respirometry/parsers/scb.py metabolon/respirometry/parsers/ccba.py metabolon/respirometry/parsers/mox.py`
- [ ] `golem --batch metabolon/resources/vitals.py metabolon/resources/reflexes.py metabolon/resources/anatomy.py`
- [ ] `golem --batch metabolon/sortase/diff_viewer.py metabolon/enzymes/circadian.py`

### Research (--full mode, needs MCP)
- [ ] `golem --max-turns 30 --full "Use rheotaxis_search to find recent AI governance news. Extract insights as structured card to ~/epigenome/chromatin/chemosensory/cards/. Include consulting angle for banking/finserv."`
- [ ] `golem --max-turns 30 --full "Use navigator to browse https://docs.bigmodel.cn/llms.txt. Extract API setup, rate limits, model list, Claude Code integration. Write reference to ~/epigenome/chromatin/Reference/zhipu-coding-plan-reference.md"`

### Fixes (learned from failed golems 2026-03-31)
- [ ] `golem --max-turns 30 "Add --provider flag to effectors/golem. Providers: zhipu (default, ZHIPU_API_KEY, https://open.bigmodel.cn/api/anthropic, GLM-5.1), volcano (VOLCANO_API_KEY, https://ark.cn-beijing.volces.com/api/coding, Doubao-Seed-2.0-Code), infini (INFINI_API_KEY, https://cloud.infini-ai.com/maas/coding, MiniMax-M2.7). Keep --batch, --max-turns, --full, --bare. Test: golem --provider volcano 'echo hello'"`
- [ ] `golem --max-turns 20 "Read effectors/cn-route. Add hosts: ark.cn-beijing.volces.com, console.volcengine.com, www.volcengine.com, docs.infini-ai.com, platform.moonshot.cn, code.kimi.com. Keep existing hosts. No sudo needed for the edit."`
- [ ] `golem --full --max-turns 30 "You have MCP tools including rheotaxis_search. Use them WITHOUT asking for permission. Research coding model benchmarks: GLM-5.1 vs Doubao-Seed-2.0-Code vs MiniMax-M2.7 vs DeepSeek-V3.2 vs Kimi-K2.5. Focus on SWE-Bench and HumanEval. Write to ~/epigenome/chromatin/Reference/golem-model-benchmark.md"`

## Running (max 4)

(none)

## Done

(move completed tasks here with result)
