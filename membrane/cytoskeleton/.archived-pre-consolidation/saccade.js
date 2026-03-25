#!/usr/bin/env node
/**
 * PreToolUse Hook - Nudge to use cerno instead of Grep for vault searches
 *
 * When Grep targets ~/notes/ (the vault), remind that cerno is the preferred
 * tool for knowledge lookups. Allow the search but surface the nudge.
 * Does NOT block — just warns, since sometimes grep is the right tool
 * (e.g., searching for exact wikilink syntax or file paths).
 */

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const path = data.tool_input?.path || '';

    // Only nudge when searching the vault
    if (path.includes('/notes') || path.includes('notes/')) {
      console.log(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow',
          message: 'Vault search detected. Consider: `cerno "<query>"` for semantic lookups (finds conceptual matches grep misses). Grep is fine for exact strings, wikilinks, or file paths.'
        }
      }));
    }
    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
});
