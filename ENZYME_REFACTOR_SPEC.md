# Enzyme Refactor Spec

> Execute these tasks in order. Each task is independent — commit after each.
> Run `python3 -m pytest assays/ -x -q` after every task to verify.
> After any file rename, `grep -r "old_name" --include='*.py' --include='*.md'` to catch stale refs.

## Task 1: Consolidate electroreception.py into gap_junction.py

**What:** Move `electroreception_read` tool from `metabolon/enzymes/electroreception.py` into `metabolon/enzymes/gap_junction.py`.

**Steps:**
1. Read both files
2. Copy the `electroreception_read` tool function and its helpers (`_extract_text`, SQL logic) into `gap_junction.py`
3. Add necessary imports to `gap_junction.py`
4. Delete `metabolon/enzymes/electroreception.py`
5. Grep for `electroreception` across the repo — update any imports
6. Run tests

**Constraint:** Do NOT rename the MCP tool — it stays `electroreception_read`.

---

## Task 2: Consolidate interphase.py into secretory.py

**What:** Move `interphase_close_daily_note` tool from `metabolon/enzymes/interphase.py` into `metabolon/enzymes/secretory.py`.

**Steps:**
1. Read both files
2. Copy the tool function into `secretory.py` (it's a write/emit action, fits with other emit_* tools)
3. Add necessary imports
4. Delete `metabolon/enzymes/interphase.py`
5. Grep for `interphase` in enzyme imports — update (note: `pinocytosis_interphase` is a different tool in pinocytosis.py, don't touch)
6. Run tests

**Constraint:** Tool name stays `interphase_close_daily_note`.

---

## Task 3: Consolidate polymerization.py into secretory.py

**What:** Move `polymerization` tool from `metabolon/enzymes/polymerization.py` into `metabolon/enzymes/secretory.py`.

**Steps:**
1. Read both files
2. Copy tool function into `secretory.py` (praxis organelle already imported there via `emit_praxis`)
3. Check for import overlap — `praxis` organelle may already be imported
4. Delete `metabolon/enzymes/polymerization.py`
5. Grep for `from metabolon.enzymes.polymerization` or `from metabolon.enzymes import polymerization`
6. Run tests

**Constraint:** Tool name stays `polymerization`.

---

## Task 4: Consolidate signaling.py into secretory.py

**What:** Move `metabolism_knowledge_signal` tool from `metabolon/enzymes/signaling.py` into `metabolon/enzymes/secretory.py`.

**Steps:**
1. Read both files
2. Copy tool function and its SensorySystem import into `secretory.py`
3. Delete `metabolon/enzymes/signaling.py`
4. Grep for stale refs
5. Run tests

**Constraint:** Tool name stays `metabolism_knowledge_signal`.

---

## Task 5: Consolidate mutation_sense.py into integrin.py

**What:** Move `proprioception_skills` tool from `metabolon/enzymes/mutation_sense.py` into `metabolon/enzymes/integrin.py`.

**Steps:**
1. Read both files
2. Copy tool function and helpers into `integrin.py`
3. Delete `metabolon/enzymes/mutation_sense.py`
4. Grep for stale refs
5. Run tests

**Constraint:** Tool name stays `proprioception_skills`.

---

## Task 6: Consolidate porta.py into pseudopod.py

**What:** Move `porta_inject` tool from `metabolon/enzymes/porta.py` into `metabolon/enzymes/pseudopod.py`.

**Steps:**
1. Read both files
2. Copy tool function into `pseudopod.py` (auth precondition for web endocytosis)
3. Add porta organelle import
4. Delete `metabolon/enzymes/porta.py`
5. Grep for stale refs (porta is also referenced in buds and skills — only update enzyme imports, not tool names)
6. Run tests

**Constraint:** Tool name stays `porta_inject`.

---

## Task 7: Rename fasti.py to chronobiology.py

**What:** Rename the enzyme file only. Tool names already use `circadian_*` prefix so no MCP tool name changes.

**Steps:**
1. `git mv metabolon/enzymes/fasti.py metabolon/enzymes/chronobiology.py`
2. `grep -r "fasti" --include='*.py' --include='*.md'` across the repo
3. Update any `from metabolon.enzymes.fasti` or `from metabolon.enzymes import fasti` imports
4. Do NOT rename the organelle (`circadian_clock.py`) — it's already bio-named
5. Do NOT rename MCP tool names (`circadian_list`, `circadian_set`, etc.) — they're already bio-named
6. Run tests

---

## Task 8: Extract endosomal business logic to organelle

**What:** Move the ~250 lines of email classification logic from `metabolon/enzymes/endosomal.py` into a new `metabolon/organelles/endosomal.py`.

**Steps:**
1. Read `metabolon/enzymes/endosomal.py`
2. Identify all non-MCP-wrapper functions: `_classify()`, `_extract_sender()`, `_sender_is_automated()`, `_extract_subject()`, `_classify_subject()`, `endosomal_pipeline()` and any helper functions
3. Create `metabolon/organelles/endosomal.py` with these functions
4. In the enzyme file, replace inline logic with imports from the new organelle
5. Enzyme functions should become thin wrappers: validate params, call organelle, format response
6. Run tests — if no endosomal tests exist, note this but don't block

**Pattern to follow:** Look at how `metabolon/enzymes/rheotaxis.py` wraps `metabolon/organelles/rheotaxis_engine.py` — that's the target pattern.

---

## Task 9: Extract gradient business logic to organelle

**What:** Move ~400 lines of sensor sensing logic from `metabolon/enzymes/gradient.py` into a new `metabolon/organelles/gradient_sense.py`.

**Steps:**
1. Read `metabolon/enzymes/gradient.py`
2. Move: `_topology_weight()`, `_score_text()`, `_sense_endocytosis()`, `_sense_signals()`, `_sense_rheotaxis()`, and aggregation/normalization logic
3. Create `metabolon/organelles/gradient_sense.py`
4. Enzyme keeps only the @tool wrapper that calls the organelle
5. Run tests

---

## Task 10: Extract receptor business logic to organelle

**What:** Move ~120 lines of goal/phase/flashcard logic from `metabolon/enzymes/receptor.py` into a new `metabolon/organelles/receptor_sense.py`.

**Steps:**
1. Read `metabolon/enzymes/receptor.py`
2. Move: `current_phase()`, `restore_goals()`, `ProprioceptiveStore` class, `decode_flashcard_deck()`, goal slug matching
3. Create `metabolon/organelles/receptor_sense.py`
4. Enzyme keeps only @tool wrappers
5. Run tests

---

## Task 11: Extract secretory chaperone check to organelle

**What:** Move `_chaperone_check()` from `metabolon/enzymes/secretory.py` into existing `metabolon/organelles/golgi.py` or `metabolon/organelles/secretory_vesicle.py`.

**Steps:**
1. Read `metabolon/enzymes/secretory.py` — find `_chaperone_check()` (PII patterns, character validation)
2. Read `metabolon/organelles/golgi.py` and `metabolon/organelles/secretory_vesicle.py` — pick the better fit
3. Move the function to the chosen organelle
4. Update import in enzyme
5. Run tests

---

## Verification

After all tasks, run:
```bash
python3 -m pytest assays/ -q
grep -r "from metabolon.enzymes.electroreception\|from metabolon.enzymes.interphase\|from metabolon.enzymes.polymerization\|from metabolon.enzymes.signaling\|from metabolon.enzymes.mutation_sense\|from metabolon.enzymes.porta\|from metabolon.enzymes.fasti" --include='*.py'
```

The grep should return zero hits. All tests should pass.

## Files touched summary

**Deleted (6):** electroreception.py, interphase.py, polymerization.py, signaling.py, mutation_sense.py, porta.py
**Renamed (1):** fasti.py -> chronobiology.py
**Modified (4):** gap_junction.py, secretory.py, integrin.py, pseudopod.py
**Created organelles (3):** endosomal.py, gradient_sense.py, receptor_sense.py
**Modified organelle (1):** golgi.py or secretory_vesicle.py
