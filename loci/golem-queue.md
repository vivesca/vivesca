# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.

## Pending

### Operons (grouped by shared context)

#### Coverage operon — test coverage tooling
- [x] `golem --provider infini --max-turns 50 "Read metabolon/sortase/validator.py AND metabolon/organelles/complement.py. Add check_test_coverage to validator (validates test coverage meets threshold). Add coverage_summary to complement (cross-refs metabolon/ vs assays/). These are related — validator uses complement's data. Write tests for both. Run pytest. Fix failures."`

#### Readiness operon — system health checks
- [x] `golem --provider infini --max-turns 50 "Read metabolon/metabolism/preflight.py AND metabolon/organelles/glycolysis_rate.py. Add check_golem_ready to preflight (verifies golem binary, API keys, provider health). Add suggest_conversions to glycolysis_rate (identifies LLM calls that could be deterministic). Write tests for both. Run pytest. Fix failures."`

#### Dispatch operon — execution infrastructure
- [x] `golem --provider infini --max-turns 50 "Read metabolon/organelles/translocon.py AND effectors/golem-daemon. Add dispatch_stats to translocon (tracks golem runs, success rate, provider breakdown). Add provider-aware concurrency to golem-daemon (parse --provider from queued commands, respect limits: zhipu=4, infini=6, volcano=8). Write tests. Run pytest. Fix failures."`

### Standalone tasks

#### Effectors
- [x] `golem --provider volcano --max-turns 50 "Create effectors/capco-prep as Python. Reads chromatin/Capco/, lists docs, flags stale, outputs readiness checklist. Test it."`
- [x] `golem --provider infini --max-turns 50 "Create effectors/weekly-status as Python. git stats, test count, calendar, outputs markdown report. Test it."`

#### Tests (remaining untested)
- [x] `golem --provider infini --batch metabolon/respirometry/parsers/ccba.py metabolon/respirometry/parsers/mox.py`
- [x] `golem --provider volcano --test metabolon/enzymes/circadian.py`

### Test batches (daemon-ready, round-robin across providers)
- [x] `golem --provider infini --batch metabolon/organelles/catabolism.py metabolon/organelles/consolidation.py metabolon/organelles/cytokinesis.py metabolon/organelles/ecphory.py metabolon/organelles/expression.py`
- [x] `golem --provider volcano --batch metabolon/organelles/glycogen.py metabolon/organelles/hemostasis.py metabolon/organelles/integrin.py metabolon/organelles/kinesin.py metabolon/organelles/operons.py`
- [x] `golem --provider infini --batch metabolon/organelles/pinocytosis.py metabolon/organelles/polarization.py metabolon/organelles/pseudopod.py metabolon/organelles/synthase.py metabolon/organelles/turgor.py`
- [x] `golem --provider volcano --batch metabolon/enzymes/auscultation.py metabolon/enzymes/demethylase.py metabolon/enzymes/differentiation.py metabolon/enzymes/electroreception.py metabolon/enzymes/emit.py`
- [x] `golem --provider infini --batch metabolon/enzymes/endocytosis.py metabolon/enzymes/endosomal.py metabolon/enzymes/gap_junction.py metabolon/enzymes/histone.py metabolon/enzymes/ingestion.py`
- [x] `golem --provider volcano --batch metabolon/enzymes/interoception.py metabolon/enzymes/lysis.py metabolon/enzymes/mitosis.py metabolon/enzymes/navigator.py metabolon/enzymes/noesis.py`
- [x] `golem --provider infini --batch metabolon/enzymes/proprioception.py metabolon/enzymes/sporulation.py metabolon/enzymes/vasomotor.py metabolon/sortase/sortase.py`
- [x] `golem --provider volcano --batch metabolon/resources/constitution.py metabolon/tachometer.py metabolon/respirometry/parsers/ccba.py metabolon/respirometry/parsers/mox.py`

### Infrastructure
- [x] `golem --provider infini --max-turns 30 "Add 'ps' subcommand to effectors/golem. Lists running golem processes (ps aux | grep claude.*--print). For each: show module name, provider (from env vars), age, and stale flag. Stale = missing --dangerously-skip-permissions OR target test file already exists in assays/. Add --kill flag to kill stale ones. Usage: golem ps, golem ps --kill. Test it."`

### Research (--full mode, needs MCP)
- [x] `golem --provider infini --full --max-turns 50 "Use rheotaxis_search to find recent AI governance news. Extract insights as structured card to ~/epigenome/chromatin/chemosensory/cards/. Include consulting angle for banking/finserv."`

## Done (2026-03-31)

- [x] golem-daemon, council, browse, --provider, cn-route — infra done
- [x] case_study CAR, chromatin stale_marks/type_counts — features done
- [x] pore, pulse, statolith, vitals, boc, diff_viewer, hsbc, scb, reflexes, anatomy — tests done (+505)
- [x] anatomy/reflexes/pore/pulse/statolith fixes — all 0 failures
