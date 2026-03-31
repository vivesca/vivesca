# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.
**NOTE: ZhiPu broken as golem provider (hangs ~180s, exit=1). Use Infini/Volcano only until diagnosed.**

## Pending

### Fixes

#### Fix sortase test failures (20 failures in 2 files)
- [ ] `golem --provider infini --max-turns 40 "Run: uv run pytest assays/test_sortase_actions.py assays/test_sortase_cli.py -v --tb=short 2>&1 | tail -80. Read both test files and the source modules they test. Diagnose each failure. Fix tests or source. Run pytest until all pass. Do NOT delete tests."`

#### Fix 6 substrate test failures
- [ ] `golem --provider volcano --max-turns 30 "Run: uv run pytest assays/test_substrate_memory.py assays/test_substrate_vasomotor.py -v --tb=short 2>&1 | tail -40. Read failing tests and source modules. Fix. Run pytest until green."`

### Test operons (Infini + Volcano only)

#### Sortase core (4 modules, ~70K)
- [ ] `golem --provider infini --max-turns 50 "Write tests for these 4 modules. Read each, write assays/test_<name>.py. Run pytest on each. Fix failures. Modules: metabolon/sortase/executor.py metabolon/sortase/decompose.py metabolon/sortase/graph.py metabolon/sortase/logger.py"`

#### Sortase tooling (6 modules, ~28K)
- [ ] `golem --provider volcano --max-turns 50 "Write tests for these 6 modules. Read each, write assays/test_<name>.py. Run pytest on each. Fix failures. Modules: metabolon/sortase/validator.py metabolon/sortase/compare.py metabolon/sortase/linter.py metabolon/sortase/coaching.py metabolon/sortase/history.py metabolon/sortase/router.py"`

#### RSS support (7 modules, ~31K)
- [ ] `golem --provider infini --max-turns 50 "Write tests for these 7 modules. Read each, write assays/test_rss_<name>.py (e.g. test_rss_log.py, test_rss_discover.py). ALL test files go in assays/ flat — NEVER create subdirectories. Run pytest. Fix failures. Modules: metabolon/organelles/endocytosis_rss/log.py metabolon/organelles/endocytosis_rss/discover.py metabolon/organelles/endocytosis_rss/cargo.py metabolon/organelles/endocytosis_rss/config.py metabolon/organelles/endocytosis_rss/state.py metabolon/organelles/endocytosis_rss/sorting.py metabolon/organelles/endocytosis_rss/migration.py"`

#### Respirometry (5 modules, ~12K)
- [ ] `golem --provider volcano --max-turns 40 "Write tests for these 5 modules. Read each, write assays/test_<name>.py. Run pytest. Fix failures. Modules: metabolon/respirometry/payments.py metabolon/respirometry/monitors.py metabolon/respirometry/detect.py metabolon/respirometry/schema.py metabolon/respirometry/categories.py"`

#### Gastrulation (4 modules, ~14K)
- [ ] `golem --provider infini --max-turns 40 "Write tests for these 4 modules. Write assays/test_gastrulation_add.py, test_gastrulation_check.py, test_gastrulation_epigenome.py, test_gastrulation_init.py. Run pytest. Fix failures. Modules: metabolon/gastrulation/add.py metabolon/gastrulation/check.py metabolon/gastrulation/epigenome.py metabolon/gastrulation/init.py"`

#### Substrates small + misc (4 modules)
- [ ] `golem --provider volcano --max-turns 40 "Write tests: assays/test_substrate_constitution.py, test_substrate_tools.py, test_substrate_spending.py, test_substrate.py. Run pytest. Fix failures. Modules: metabolon/metabolism/substrates/constitution.py metabolon/metabolism/substrates/tools.py metabolon/metabolism/substrates/spending.py metabolon/metabolism/substrate.py"`

#### Lysin + misc (6 modules)
- [ ] `golem --provider infini --max-turns 40 "Write tests: assays/test_lysin_fetch.py, test_lysin_format.py, test_endosomal_organelle.py, test_endosomal_enzyme.py, test_morphology_base.py, test_codons_templates_unit.py. Run pytest. Fix failures. Modules: metabolon/lysin/fetch.py metabolon/lysin/format.py metabolon/organelles/endosomal.py metabolon/enzymes/endosomal.py metabolon/morphology/base.py metabolon/codons/templates.py"`

#### Small modules (5 modules)
- [ ] `golem --provider volcano --max-turns 40 "Write tests: assays/test_pinocytosis_photoreception.py, test_pinocytosis_ultradian.py, test_pinocytosis_ecdysis.py, test_organelle_sporulation.py, test_resource_constitution.py. Run pytest. Fix failures. Modules: metabolon/pinocytosis/photoreception.py metabolon/pinocytosis/ultradian.py metabolon/pinocytosis/ecdysis.py metabolon/organelles/sporulation.py metabolon/resources/constitution.py"`

### Compound infra

#### Golem summary cleanup
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem. The summary subcommand has duplicate python heredocs. Deduplicate — keep _run_summary, pass --recent via env var or arg. Update assays/test_golem_summary.py. Run pytest. Fix failures."`

## Done (2026-03-31)

- [x] daemon pytest gate (volcano) — mark_failed + check_new_test_files_and_run_pytest
- [x] vasomotor_core tests (volcano, 31 passed)
- [x] RSS core tests (volcano, 81 passed)
- [x] substrate_hygiene/memory/vasomotor tests (infini, 153 passed, 6 failed)
- [x] golem_daemon tests (volcano, 16 passed)
