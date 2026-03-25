#!/usr/bin/env node
/**
 * Stop Hook - Check for uncommitted changes across key repos
 *
 * At session end, warns if any tracked repo has dirty state.
 * Prevents losing work that was never committed.
 */

const { execSync } = require('child_process');
const path = require('path');

const REPOS = [
  { name: 'reticulum', path: path.join(process.env.HOME, 'reticulum') },
  { name: 'skills', path: path.join(process.env.HOME, 'skills') },
  { name: 'notes', path: path.join(process.env.HOME, 'notes') },
];

try {
  const dirty = [];

  for (const repo of REPOS) {
    try {
      const status = execSync(`git -C "${repo.path}" status --porcelain`, {
        encoding: 'utf8',
        timeout: 5000,
      }).trim();

      if (status) {
        const count = status.split('\n').length;
        dirty.push(`${repo.name} (${count} file${count > 1 ? 's' : ''})`);
      }
    } catch {
      // Skip repos that don't exist or aren't git repos
    }
  }

  if (dirty.length > 0) {
    console.log(`⚠️  Uncommitted changes: ${dirty.join(', ')}. Commit before closing.`);
  }
} catch {
  // Don't block session end on hook errors
}
