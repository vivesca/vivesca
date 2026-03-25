---
name: debridement
description: Sweep vivesca for naming violations and stale references. Cell concepts get bio names; runtime mechanics keep Python names. "debridement", "naming sweep", "bio names", "stale references", "naming violations".
user_invocable: true
model: sonnet
context: fork
---

# Debridement — Naming Sweep

Debridement removes necrotic tissue before it harbors infection. In vivesca, the necrotic tissue is non-bio names in cell-concept positions and stale references to deleted paths. This skill IS the sweep.

**The rule:** cell concepts get bio names; runtime mechanics (Python keywords, framework conventions, `__dunder__`, `self`, `cls`) keep Python names. Forced violations are not cosmetic — they signal confused architecture.

---

## Step 1 — Non-Bio Name Detection

### Module names under cytoplasm/metabolon/ that aren't biological

```bash
ls /Users/terry/code/vivesca/cytoplasm/metabolon/
```

Flag any directory or `.py` file whose name is a generic English word (helper, utils, manager, handler, client, service, loader, parser, processor, runner, worker, base, common, core, main, shared, misc).

### Class names that aren't biological

```python
# Run from vivesca root
grep -rn "^class " /Users/terry/code/vivesca/cytoplasm/ \
  /Users/terry/code/vivesca/membrane/ \
  /Users/terry/code/vivesca/effectors/ \
  --include="*.py" | head_limit: 60
```

Flag class names that are generic (Manager, Handler, Client, Service, Processor, Runner, Worker, Base, Mixin, Helper, Loader, Parser, Builder, Factory, Adapter).

### Public function names using generic verbs where bio names would fit

Generic verbs to flag in public function positions (not private/dunder):

```python
grep -rn "^\s*def \(gather\|fetch\|send\|read\|write\|log\|start\|stop\|run\|get\|set\|update\|process\|handle\|execute\|perform\|do_\)\b" \
  /Users/terry/code/vivesca/cytoplasm/ \
  --include="*.py" | head_limit: 40
```

Private methods (`_fetch`, `__send__`) are exempt — runtime mechanics.

### Variable names referencing old/deleted identities

```python
grep -rn "\bllm\b\|\bcopia\b\|\bkairos\b\|\bcommute\b\|\bacta\b\|\breticulum\b" \
  /Users/terry/code/vivesca/ \
  --include="*.py" --include="*.md" --include="*.json" \
  --exclude-dir=".git" | head_limit: 40
```

---

## Step 2 — Stale Reference Detection

### References to deleted paths

```bash
grep -rn "cofactors/\|~/bin/\b\|reticulum/" \
  /Users/terry/code/vivesca/ \
  --include="*.py" --include="*.md" --include="*.json" \
  --exclude-dir=".git" | head_limit: 30
```

### Dead sys.path hacks

```python
grep -rn "sys\.path\." /Users/terry/code/vivesca/ \
  --include="*.py" --exclude-dir=".git" | head_limit: 20
```

### Comments mentioning old names

```bash
grep -rn "#.*\(llm\|copia\|kairos\|reticulum\|acta\b\|commute\)" \
  /Users/terry/code/vivesca/ \
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

## Scope

Default sweep covers:

- `/Users/terry/code/vivesca/cytoplasm/`
- `/Users/terry/code/vivesca/membrane/`
- `/Users/terry/code/vivesca/effectors/`
- `/Users/terry/code/vivesca/receptors/` (SKILL.md frontmatter names only)
- `/Users/terry/code/vivesca/anatomy.md`

If user specifies a subdirectory or file, scope to that.
