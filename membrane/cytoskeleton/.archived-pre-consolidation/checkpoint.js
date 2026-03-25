#!/usr/bin/env node
/**
 * Stop Hook - Contract Enforcer
 *
 * Blocks session termination if any active CONTRACT file has unchecked items.
 * Contracts live in ~/.claude/contracts/*.md
 * Created by tasks via the `contract` skill.
 */

const fs = require('fs');
const path = require('path');

const CONTRACTS_DIR = path.join(process.env.HOME, '.claude', 'contracts');

try {
  if (!fs.existsSync(CONTRACTS_DIR)) {
    process.exit(0);
  }

  const files = fs.readdirSync(CONTRACTS_DIR).filter(f => f.endsWith('.md'));

  if (files.length === 0) {
    process.exit(0);
  }

  const blockers = [];

  for (const file of files) {
    const content = fs.readFileSync(path.join(CONTRACTS_DIR, file), 'utf8');
    const unchecked = (content.match(/^- \[ \]/gm) || []).length;
    if (unchecked > 0) {
      blockers.push(`${file}: ${unchecked} unchecked item${unchecked > 1 ? 's' : ''}`);
    }
  }

  if (blockers.length > 0) {
    console.log(
      `🔴 CONTRACT NOT FULFILLED — cannot terminate:\n` +
      blockers.map(b => `  • ${b}`).join('\n') +
      `\n\nComplete all items or run: /contract clear <name>`
    );
    process.exit(2);
  }

} catch {
  // Never block on hook errors
  process.exit(0);
}
