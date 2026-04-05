# Test Coverage Audit

## Untested modules (no corresponding test file)
| Module | Lines | Priority |
|--------|-------|----------|
| metabolon/checkpoint.py | 300 | high |
| metabolon/codons/templates.py | 119 | high |
| metabolon/cytosol.py | 89 | med |
| metabolon/enzymes/circadian.py | 92 | med |
| metabolon/enzymes/endocytosis.py | 220 | high |
| metabolon/enzymes/endosomal.py | 148 | high |
| metabolon/enzymes/rheotaxis.py | 53 | med |
| metabolon/enzymes/sortase.py | 214 | high |
| metabolon/locus.py | 98 | med |
| metabolon/metabolism/mismatch_repair.py | 342 | high |
| metabolon/metabolism/substrate.py | 55 | med |
| metabolon/metabolism/substrates/constitution.py | 140 | high |
| metabolon/metabolism/substrates/hygiene.py | 293 | high |
| metabolon/metabolism/substrates/memory.py | 278 | high |
| metabolon/metabolism/substrates/mismatch_repair.py | 185 | high |
| metabolon/metabolism/substrates/operon_monitor.py | 152 | high |
| metabolon/metabolism/substrates/spending.py | 91 | med |
| metabolon/metabolism/substrates/tools.py | 115 | high |
| metabolon/metabolism/substrates/vasomotor.py | 634 | high |
| metabolon/morphology/base.py | 64 | med |
| metabolon/operons.py | 193 | high |
| metabolon/organelles/chromatin.py | 237 | high |
| metabolon/organelles/endosomal.py | 321 | high |
| metabolon/organelles/statolith.py | 2045 | high |
| metabolon/organelles/tests/test_moneo.py | 503 | high |
| metabolon/pathways/overnight.py | 159 | high |
| metabolon/perfusion.py | 109 | high |
| metabolon/pinocytosis/ecdysis.py | 23 | low |
| metabolon/pinocytosis/interphase.py | 166 | high |
| metabolon/pinocytosis/photoreception.py | 24 | low |
| metabolon/pinocytosis/ultradian.py | 25 | low |
| metabolon/pore.py | 2320 | high |
| metabolon/pulse.py | 1162 | high |
| metabolon/resources/anatomy.py | 649 | high |
| metabolon/resources/chromatin_stats.py | 7 | low |
| metabolon/resources/circadian.py | 7 | low |
| metabolon/resources/consolidation.py | 5 | low |
| metabolon/resources/constitution.py | 9 | low |
| metabolon/resources/glycogen.py | 7 | low |
| metabolon/resources/operons.py | 47 | low |
| metabolon/resources/oscillators.py | 176 | high |
| metabolon/resources/proteome.py | 112 | high |
| metabolon/resources/receptome.py | 96 | med |
| metabolon/resources/reflexes.py | 88 | med |
| metabolon/resources/vitals.py | 94 | med |
| metabolon/respiration.py | 342 | high |
| metabolon/sortase/coaching_cli.py | 64 | med |
| metabolon/sortase/diff_viewer.py | 92 | med |
| metabolon/sortase/graph.py | 393 | high |
| metabolon/symbiont.py | 288 | high |
| metabolon/vasomotor.py | 1216 | high |

## Undertested (<5 test functions)
| Module | Test file | Tests | Lines |
|--------|-----------|-------|-------|
| metabolon/enzymes/assay.py | test_assay_actions.py | 4 | 44 |
| metabolon/enzymes/auscultation.py | test_auscultation_actions.py | 3 | 129 |
| metabolon/enzymes/proteasome.py | test_proteasome_actions.py | 3 | 166 |
| metabolon/enzymes/differentiation.py | test_differentiation_actions.py | 4 | 84 |
| metabolon/enzymes/efferens.py | test_efferens_actions.py | 4 | 51 |
| metabolon/enzymes/emit.py | test_emit_actions.py | 4 | 330 |
| metabolon/enzymes/expression.py | test_expression_actions.py | 3 | 166 |
| metabolon/enzymes/ingestion.py | test_ingestion_actions.py | 3 | 107 |
| metabolon/enzymes/lysozyme.py | test_lysozyme_actions.py | 3 | 35 |
| metabolon/enzymes/mitosis.py | test_mitosis_actions.py | 3 | 80 |
| metabolon/enzymes/noesis.py | test_noesis_actions.py | 4 | 69 |
| metabolon/enzymes/polarization.py | test_polarization_actions.py | 3 | 160 |
| metabolon/enzymes/sporulation.py | test_sporulation_actions.py | 4 | 276 |
| metabolon/enzymes/turgor.py | test_turgor_actions.py | 3 | 131 |
| metabolon/lysin/format.py | test_lysin_format.py | 4 | 45 |
| metabolon/membrane.py | test_membrane.py | 3 | 358 |
| metabolon/metabolism/repair.py | test_repair.py | 1 | 88 |
| metabolon/metabolism/sweep.py | test_sweep.py | 4 | 113 |
| metabolon/organelles/endocytosis_rss/cli.py | test_endocytosis_rss_cli.py | 2 | 724 |
| metabolon/organelles/endocytosis_rss/discover.py | test_endocytosis_rss_discover.py | 3 | 190 |
| metabolon/organelles/endocytosis_rss/migration.py | test_endocytosis_rss_migration.py | 4 | 62 |
| metabolon/organelles/engram.py | test_engram.py | 4 | 1153 |
| metabolon/organelles/entrainment.py | test_entrainment.py | 3 | 209 |
| metabolon/organelles/metabolism_loop.py | test_metabolism_loop.py | 3 | 571 |
| metabolon/organelles/polarization_loop.py | test_polarization_loop.py | 3 | 635 |
| metabolon/organelles/sporulation.py | test_sporulation_actions.py | 4 | 283 |
| metabolon/pinocytosis/polarization.py | test_polarization_actions.py | 3 | 385 |
| metabolon/sortase/compare.py | test_sortase_compare.py | 4 | 197 |

## Well-tested: 100 modules

## Summary
- Total: 179
- Untested: 51
- Undertested: 28
- Well-tested: 100
