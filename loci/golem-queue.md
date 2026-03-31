# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.

## Pending

### Compound infra (build the machine that builds)

#### Golem enhancement — enriched logging + summary subcommand
- [x] `golem --provider infini --max-turns 50 "Read effectors/golem AND loci/plans/golem-compound-infra.md. Implement enhancements 1 and 3 from the spec: (1) After claude finishes in _run_golem, count new files via git diff, run pytest on any new assays/test_*.py files, parse pass/fail, add files_created/tests_passed/tests_failed/pytest_exit to the JSONL log line. (2) Add a 'summary' subcommand — golem summary reads GOLEM_LOG JSONL and prints a provider stats table (runs, pass, fail, avg duration, tests created). Support --recent N flag. Use python for the summary since jq may not be installed. Write tests in assays/test_golem_summary.py. Run pytest. Fix failures."`

#### Daemon enhancement — post-dispatch pytest gate
- [x] `golem --provider volcano --max-turns 50 "Read effectors/golem-daemon AND loci/plans/golem-compound-infra.md. Implement enhancement 2: after a golem task completes with exit=0, check git diff for new assays/test_*.py files, run pytest on them, log result. If pytest fails mark task as [!] instead of [x]. The mark_failed function already exists in golem-daemon. Update assays/test_golem_daemon.py with tests for the new behavior (note: the test loads golem-daemon via exec with __name__='golem_daemon' to avoid sys.exit). Run pytest. Fix failures."`

### Fixes (heal first)

#### Fix sortase test failures (20 failures across 2 files)
- [!] `golem --provider zhipu --max-turns 40 "Run: uv run pytest assays/test_sortase_actions.py assays/test_sortase_cli.py -v --tb=short 2>&1 | tail -80. Read both test files and the source modules they test (metabolon/sortase/sortase.py, metabolon/enzymes/sortase.py, metabolon/sortase/router.py). Diagnose each failure. Fix tests or source as needed. Run pytest on both files until all pass. Do NOT delete tests — fix them."`

### Operons — tests (reset failed Infini tasks, spread across all providers)

#### Sortase core operon (4 modules, ~70K)
- [ ] `golem --provider infini --max-turns 50 "Write tests for these 4 modules. Read each, write assays/test_<name>.py. Run pytest on each. Fix failures. Modules: metabolon/sortase/executor.py metabolon/sortase/decompose.py metabolon/sortase/graph.py metabolon/sortase/logger.py"`

#### RSS core operon (4 modules, ~92K)
- [x] `golem --provider volcano --max-turns 50 "Write tests for these 4 modules. Read each, write assays/test_<name>.py. Run pytest on each. Fix failures. Modules: metabolon/organelles/endocytosis_rss/fetcher.py metabolon/organelles/endocytosis_rss/digest.py metabolon/organelles/endocytosis_rss/breaking.py metabolon/organelles/endocytosis_rss/relevance.py"`

#### Substrates big operon (3 modules, ~45K)
- [x] `golem --provider infini --max-turns 50 "Write tests for these 3 modules. Read each, write assays/test_<name>.py (test_substrate_vasomotor.py, test_substrate_hygiene.py, test_substrate_memory.py). Run pytest. Fix failures. Modules: metabolon/metabolism/substrates/vasomotor.py metabolon/metabolism/substrates/hygiene.py metabolon/metabolism/substrates/memory.py"`

#### Vasomotor standalone (45K)
- [x] `golem --provider volcano --max-turns 50 "Write thorough tests for metabolon/vasomotor.py (45K lines). Read carefully, write assays/test_vasomotor_core.py. Focus on pure functions and data transformations. Mock external calls. Run pytest. Fix failures."`

#### Resources batch
- [x] `golem --provider zhipu --batch metabolon/resources/constitution.py metabolon/resources/glycogen.py metabolon/resources/chromatin_stats.py metabolon/resources/consolidation.py`

#### Small batch
- [ ] `golem --provider zhipu --batch metabolon/morphology/base.py metabolon/pinocytosis/photoreception.py metabolon/pinocytosis/ultradian.py metabolon/pinocytosis/ecdysis.py metabolon/organelles/sporulation.py`

## Done (2026-03-31)

### ZhiPu tasks (confirmed ran)
- [x] Sortase tooling operon (6 modules) — zhipu
- [x] RSS support operon (7 modules) — zhipu
- [x] Respirometry operon (5 modules) — zhipu
- [x] Gastrulation operon (4 modules) — zhipu
- [x] Substrates small operon (4 modules) — zhipu
- [x] Lysin operon (2 modules) — zhipu
- [x] Endosomal (2 modules) — zhipu
- [x] Codons templates — zhipu

### Prior batches
- [x] golem-daemon, council, browse, --provider, cn-route — infra done
- [x] case_study CAR, chromatin stale_marks/type_counts — features done
- [x] pore, pulse, statolith, vitals, boc, diff_viewer, hsbc, scb, reflexes, anatomy — tests done (+505)
- [x] anatomy/reflexes/pore/pulse/statolith fixes — all 0 failures
