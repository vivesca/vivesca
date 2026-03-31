# Golem Task Queue

Tasks waiting for dispatch. CC adds, golem consumes. Keep ~10 tasks ahead.

## Pending

- [ ] `golem --max-turns 30 "Read metabolon/organelles/engagement_scope.py. Add debrief function. Write tests. Run pytest. Fix failures."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/complement.py. Add coverage_summary function. Write tests. Run pytest. Fix failures."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/talking_points.py. Add weekly_refresh function. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/case_study.py. Add generate_from_template with CAR framework. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/sortase/validator.py. Add check_test_coverage validation. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/translocon.py. Add dispatch_stats function. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/metabolism/preflight.py. Add check_golem_ready. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/glycolysis_rate.py. Add suggest_conversions. Write tests. Run pytest."`
- [ ] `golem --max-turns 30 "Read metabolon/organelles/chromatin.py. Add stale_marks and type_counts methods. Write tests. Run pytest."`
- [ ] `golem --max-turns 40 --batch metabolon/pore.py metabolon/pulse.py metabolon/organelles/statolith.py`
- [ ] `golem "Create effectors/capco-prep — reads chromatin/Capco/, lists docs, flags stale, outputs readiness checklist"`
- [ ] `golem "Create effectors/weekly-status — git stats, test count, calendar, outputs markdown report"`

## Running (max 4)

- mox.py tests
- reflexes.py tests  
- engagement_scope debrief feature
- complement coverage_summary feature

- [ ] `golem --max-turns 30 --full "Use navigator to browse https://docs.bigmodel.cn/llms.txt and discover all available documentation pages. Then extract and read the most important pages about: API setup, rate limits, pricing, model list, Claude Code integration, coding plan details. Write a comprehensive reference document to ~/epigenome/chromatin/Reference/zhipu-coding-plan-reference.md with all technical details, exact endpoints, model names, rate limits, pricing tiers. Include everything needed to configure and troubleshoot golem."`
- [ ] `golem --max-turns 30 --full "Use navigator to browse https://platform.minimaxi.com/docs/pricing/overview and follow links to all pricing pages. Extract complete pricing for Token Plan, Coding Plan, pay-as-you-go. Write reference to ~/epigenome/chromatin/Reference/minimax-pricing-reference.md with all tiers, prices in RMB, quotas, rate limits, model names, API endpoints, CC compatibility setup."`

- [ ] `golem --max-turns 30 "Build effectors/browse as a Python script. A reliable web content extractor that chains fallbacks: 1) defuddle parse URL --md, 2) if empty, curl URL and extract text, 3) if still empty, print NEEDS_BROWSER. Usage: browse URL [--raw]. Output: clean markdown to stdout. Handle redirects, encoding, timeouts. Test with: browse https://platform.minimaxi.com/docs/guides/pricing-token-plan && browse https://news.ycombinator.com && browse https://github.com"`

## Done

(move completed tasks here with result)
