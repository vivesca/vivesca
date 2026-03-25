#!/usr/bin/env node
/**
 * PreToolUse Hook - Glob tool guard
 *
 * Blocks recursive glob patterns on the home directory (times out).
 * Must scope to a subdirectory.
 */

const fs = require('fs');

function logDeny(hookName, reason) {
  try {
    const entry = JSON.stringify({ ts: new Date().toISOString(), hook: hookName, rule: reason.slice(0, 80) }) + '\n';
    fs.appendFileSync('/Users/terry/logs/hook-fire-log.jsonl', entry);
  } catch (_) {}
}

function deny(reason) {
  logDeny('glob-guard', reason);
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason
    }
  }));
  process.exit(0);
}

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const pattern = data.tool_input?.pattern || '';
    const searchPath = data.tool_input?.path || '';

    // Block recursive patterns on home directory
    if (pattern.includes('**')) {
      const homePaths = [
        '/Users/terry',
        '$HOME',
      ];

      // If path is home dir or unset (defaults to cwd which could be ~)
      const isHome = homePaths.some(h => searchPath === h || searchPath === h + '/');
      const isUnscoped = searchPath === '' || searchPath === undefined;

      if (isHome) {
        deny('Glob ** on /Users/terry times out. Scope to a subdirectory: ~/notes/, ~/code/, ~/docs/, etc.');
      }

      // If path not set, we can't be sure — allow but the CLAUDE.md rule still applies
    }

    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
});
