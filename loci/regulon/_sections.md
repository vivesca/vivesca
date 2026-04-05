# Sections

Defines coaching rule categories, their ordering, impact, and filename prefixes.

---

## 1. Code Patterns (code)

**Impact:** CRITICAL
**Description:** Python syntax, imports, return types, and code structure. Most common source of ribosome failures.

## 2. Execution Discipline (exec)

**Impact:** HIGH
**Description:** Workflow steps: TDD, ast.parse, verify, commit. The process that prevents silent failures.

## 3. Exploration Tasks (explore)

**Impact:** MEDIUM
**Description:** Batch commands, turn budgeting, output-first. For audit and classification dispatches.

## 4. Context Management (context)

**Impact:** MEDIUM
**Description:** Data vs instructions, output priority, inline tasks. Prevents GLM confusion about what to do.

## 5. Spec Compliance (spec)

**Impact:** HIGH
**Description:** Follow format, execute spec only, specs are instructions. Prevents scope creep and format drift.

## 6. Article Analysis (analysis)

**Impact:** MEDIUM
**Description:** Source bias, coverage breadth, use case extraction. For content processing dispatches.

## 7. Verification (verify)

**Impact:** CRITICAL
**Description:** Silent failure detection, verify-the-verify, no placeholders. The last line of defense.

## 8. Environment (env)

**Impact:** HIGH
**Description:** Platform paths, stdin, secrets, API errors. Platform-specific gotchas.

## 9. Testing (test)

**Impact:** HIGH
**Description:** Effector testing patterns, test file placement, pytest conventions.

## 10. Dispatch & Reporting (dispatch)

**Impact:** MEDIUM
**Description:** Status reporting, delegation safety, multi-task coordination, commit messages.

## 11. File Operations (fileops)

**Impact:** HIGH
**Description:** Edit vs rewrite, file hygiene, syntax edge cases.

## 12. Backend-Specific (backend)

**Impact:** MEDIUM
**Description:** Codex, Gemini, and GLM-specific constraints and workarounds.
