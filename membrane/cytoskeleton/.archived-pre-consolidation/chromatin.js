#!/usr/bin/env node
/**
 * PostToolUse Hook - MEMORY.md budget check
 *
 * After any write/edit to MEMORY.md, counts lines and warns if over budget.
 * Uses stderr (non-blocking warning), not deny — the write already happened.
 */

const fs = require('fs');

const MEMORY_PATH = process.env.HOME + '/.claude/projects/-Users-terry/memory/MEMORY.md';
const BUDGET = 150;

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = data.tool_input?.file_path || '';

    // Only check if the file written is MEMORY.md
    if (!filePath.includes('MEMORY.md')) {
      process.exit(0);
    }

    // Count lines
    const content = fs.readFileSync(MEMORY_PATH, 'utf8');
    const lineCount = content.split('\n').length;

    if (lineCount > BUDGET) {
      // Emit warning via stderr (model sees this as tool output context)
      process.stderr.write(
        `⚠️  MEMORY.md is ${lineCount} lines (budget: ${BUDGET}). ` +
        `Demote provisional entries to ~/docs/solutions/memory-overflow.md before next /ecdysis.\n`
      );
    }

    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
});
