---
name: debridement
description: Sweep skill names for violations and stale references. "naming sweep"
user_invocable: true
model: sonnet
context: fork
---

# Debridement — Naming Sweep

Debridement removes necrotic tissue before it harbors infection. In vivesca, the necrotic tissue is non-bio names in cell-concept positions and stale references to deleted paths. This skill IS the sweep.

**The rule:** cell concepts get bio names; runtime mechanics (Python keywords, framework conventions, `__dunder__`, `self`, `cls`) keep Python names. Forced violations are not cosmetic — they signal confused architecture.

**Layer convention:** MCP enzymes (tools) = objects (enzymes, proteins, structural molecules). Skills (workflows) = processes. Organelles = system/function names. A tool named after a process is a design smell: either rename to the single object it maps to, or decompose the tool into focused pieces that each map to one object. Use `lysin` to find the correct enzyme — if no single enzyme fits, the tool needs splitting, not renaming.

---

## Step 0 — Droid Recon (free)

Before CC runs the sweep, use droid explore to gather the raw inventory:
```bash
ribosome -m "custom:glm-4.7" --cwd ~/germline \
  "List all module names, class names, and public function names under metabolon/, membrane/, and effectors/. Flag any that are generic English words (helper, utils, manager, handler, etc.) vs biological names. Also list any sys.path hacks or references to deleted paths (cofactors/, ~/bin/, reticulum/)."
```

CC then reviews the droid output for false positives and applies the homology test (Step 3). Droid scans, CC judges.

## Step 1 — Non-Bio Name Detection

### Module names under metabolon/ that aren't biological

```bash
ls ~/germline/metabolon/
```

Flag any directory or `.py` file whose name is a generic English word (helper, utils, manager, handler, client, service, loader, parser, processor, runner, worker, base, common, core, main, shared, misc).

### Class names that aren't biological

```python
# Run from vivesca root
grep -rn "^class " ~/germline/metabolon/ \
  ~/germline/membrane/ \
  ~/germline/effectors/ \
  --include="*.py" | head_limit: 60
```

Flag class names that are generic (Manager, Handler, Client, Service, Processor, Runner, Worker, Base, Mixin, Helper, Loader, Parser, Builder, Factory, Adapter).

### Public function names using generic verbs where bio names would fit

Generic verbs to flag in public function positions (not private/dunder):

```python
grep -rn "^\s*def \(gather\|fetch\|send\|read\|write\|log\|start\|stop\|run\|get\|set\|update\|process\|handle\|execute\|perform\|do_\)\b" \
  ~/germline/metabolon/ \
  --include="*.py" | head_limit: 40
```

Private methods (`_fetch`, `__send__`) are exempt — runtime mechanics.

### Variable names referencing old/deleted identities

```python
grep -rn "\bllm\b\|\bpoiesis\b\|\bkairos\b\|\bcommute\b\|\befferens\b\|\breticulum\b" \
  ~/germline/metabolon/ \
  --include="*.py" --include="*.md" --include="*.json" \
  --exclude-dir=".git" | head_limit: 40
```

---

## Step 2 — Stale Reference Detection

### References to deleted paths

```bash
grep -rn "cofactors/\|~/bin/\b\|reticulum/" \
  ~/germline/metabolon/ \
  --include="*.py" --include="*.md" --include="*.json" \
  --exclude-dir=".git" | head_limit: 30
```

### Dead sys.path hacks

```python
grep -rn "sys\.path\." ~/germline/metabolon/ \
  --include="*.py" --exclude-dir=".git" | head_limit: 20
```

### Comments mentioning old names

```bash
grep -rn "#.*\(llm\|poiesis\|kairos\|reticulum\|efferens\b\|commute\)" \
  ~/germline/metabolon/ \
  --include="*.py" --exclude-dir=".git" | head_limit: 20
```

---

## Step 3 — Homology Check

For each bio name found in the sweep, ask the homology test:

> Does this name share a **mechanism** with its biological referent, or only a **surface resemblance**?

- **Homology (keep):** the biological structure solves the same class of problem — membrane filters what enters/exits, exocytosis packages and routes output to the environment, metabolon co-localizes enzymes for a shared pathway. The name generates a design question.
- **Analogy (flag):** name is decorative. "neuron" for a logging class. "genome" for a config dict that doesn't replicate. The name tells you nothing about what the component should do next.

Run a spot-check on any bio names found during steps 1-2 that feel forced. Look for names where you can't complete the sentence: "The biology tells us this component should also _____."

---

## Step 4 — Structured Report

Produce a report with this structure:

```markdown
## Debridement Report — {date}

### RENAME REQUIRED
(wrong name in cell-concept position, architecture confused)
- path/to/file.py: `ClassName` — generic, no bio mapping
  Rx: rename to `{BioName}` ({one-line mechanism justification})

### STALE REFERENCE
(dead path, deleted name, unreachable import)
- path/to/file.py:42 — references `cofactors/` (deleted)
  Rx: remove or reroute

### HOMOLOGY FAILURE
(bio name present but surface-only — name generates no design question)
- path/to/file.py: `Neuron` — logging class, no signaling mechanism
  Rx: rename to something that earns its biology

### COSMETIC
(old comment, harmless alias, no behavior change needed)
- path/to/file.py:17 — comment references old name `llm`
  Rx: update comment

### CLEAN
Summary of areas with no violations found.
```

Severity order: RENAME REQUIRED > STALE REFERENCE > HOMOLOGY FAILURE > COSMETIC.

Do not report private/dunder names, framework conventions (Flask route names, pytest fixtures, `__init__`), or Python builtins. Those are runtime mechanics, not cell concepts.

---

## Step 5 — Skill Format Validation

For each SKILL.md in `receptors/`:

| Check | Pass | Fail |
|-------|------|------|
| Description starts with verb/trigger phrase | "Use when...", "Fetch...", "Coach..." | "A tool that..." |
| Description < 1024 chars | Short, trigger-focused | Long, summarizes workflow |
| Body < 500 lines | Concise | Bloated — split into references/ |
| No "When to Use" section duplicating description | Trigger logic in description only | Redundant trigger logic in body |
| No auxiliary files | Only SKILL.md + scripts/ + references/ + agents/ | README.md, CHANGELOG.md, etc. |
| Frontmatter has name + description | Both present | Missing field |

Report violations alongside naming results. This catches skill rot before it accumulates.

---

## Scope

Default sweep covers:

- `~/germline/metabolon/`
- `~/germline/membrane/`
- `~/germline/effectors/`
- `~/germline/membrane/receptors/` (SKILL.md frontmatter names only)
- `~/germline/anatomy.md`

If user specifies a subdirectory or file, scope to that.
