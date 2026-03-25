#!/usr/bin/env node
/**
 * PostToolUse Hook — Python chaperone (syntactic + semantic).
 *
 * After Edit/Write on .py files:
 * 1. ruff format (syntactic — protein folding)
 * 2. py_compile (semantic — does it parse?)
 * 3. Test discovery — if test_<module>.py exists, run it (semantic — does it work?)
 *
 * Bio: chaperone proteins assist folding AND verify the protein functions correctly.
 * A chaperone that only checks shape but not function is incomplete.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = data.tool_input?.file_path;

    if (!filePath || !/\.py$/.test(filePath) || filePath.includes('/notes/')) {
      console.log(input);
      return;
    }

    // 1. Syntactic: ruff format
    try {
      execSync(`ruff format "${filePath}"`, {
        cwd: path.dirname(filePath),
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 10000
      });
      execSync(`ruff check --fix "${filePath}"`, {
        cwd: path.dirname(filePath),
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 10000
      });
    } catch (e) {
      // ruff not available or failed - silent
    }

    // 2. Semantic: py_compile — does it even parse?
    try {
      execSync(`python3 -m py_compile "${filePath}"`, {
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 5000
      });
    } catch (e) {
      const stderr = e.stderr ? e.stderr.toString().trim() : '';
      if (stderr) {
        console.error(`[chaperone-py] Compile error: ${stderr.slice(0, 300)}`);
      }
    }

    // 3. Semantic: test discovery — run matching test if it exists
    const basename = path.basename(filePath, '.py');
    const dir = path.dirname(filePath);

    // Skip test discovery for non-source files
    if (basename.startsWith('test_') || basename.startsWith('.') || filePath.includes('/hooks/')) {
      console.log(input);
      return;
    }

    // Look for matching test files
    const testCandidates = [
      path.join(dir, `test_${basename}.py`),                    // same dir
      path.join(dir, 'tests', `test_${basename}.py`),           // tests/ subdir
      path.join(dir, '..', 'tests', `test_${basename}.py`),     // parent tests/
    ];

    const testFile = testCandidates.find(f => fs.existsSync(f));

    if (testFile) {
      try {
        // Find pyproject.toml or setup.py to determine project root
        let projectRoot = dir;
        let d = dir;
        while (d !== path.dirname(d)) {
          if (fs.existsSync(path.join(d, 'pyproject.toml')) || fs.existsSync(path.join(d, 'setup.py'))) {
            projectRoot = d;
            break;
          }
          d = path.dirname(d);
        }

        const result = execSync(`uv run pytest "${testFile}" -x -q 2>&1 || true`, {
          cwd: projectRoot,
          encoding: 'utf8',
          timeout: 30000
        });

        // Only report failures, not successes
        if (result.includes('FAILED') || result.includes('ERROR')) {
          const lines = result.split('\n').filter(l =>
            l.includes('FAILED') || l.includes('ERROR') || l.includes('assert')
          ).slice(0, 5);
          console.error(`[chaperone-py] Test regression in ${path.basename(testFile)}:\n${lines.join('\n')}`);
        }
      } catch (e) {
        // Test runner not available or timeout - silent
      }
    }

    console.log(input);
  } catch (err) {
    console.log(input);
  }
});
