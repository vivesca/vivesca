#!/usr/bin/env node
/**
 * PreToolUse Hook - Write/Edit guard
 *
 * Blocks writes to sensitive files (credentials, secrets, env vars).
 * Blocks writes to past daily notes (immutable historical records).
 */

const fs = require('fs');

function logDeny(hookName, reason) {
  try {
    const entry = JSON.stringify({ ts: new Date().toISOString(), hook: hookName, rule: reason.slice(0, 80) }) + '\n';
    fs.appendFileSync('~//logs/hook-fire-log.jsonl', entry);
  } catch (_) {}
}

function deny(reason) {
  logDeny('write-guard', reason);
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
    const filePath = data.tool_input?.file_path || '';

    // ~/.claude/skills/ contains symlinks to ~/skills/ — both paths resolve to the same files.
    // Previously blocked with a redirect message, but fired 102 times in 14 days with no learning.
    // Tier 1 fix: allow silently. The symlinks make it safe. Git tracks ~/skills/ regardless.
    // (Removed: was the #1 hook fire at 59% of all fires)

    const sensitivePatterns = [
      /\.secrets$/,
      /\.secrets\.d\//,
      /\.env$/,
      /\.env\.local$/,
      /\.pypirc$/,
      /credentials\.json$/,
      /[\/.]keychain\.(json|db|plist)$/i,  // actual keychain files, not source files named keychain.rs
    ];

    if (sensitivePatterns.some(p => p.test(filePath))) {
      deny(`Write to sensitive file blocked: ${filePath}. Credentials belong in macOS Keychain.`);
    }

    // Block .venv references in LaunchAgent plists
    if (/\.plist$/.test(filePath)) {
      const content = data.tool_input?.content || data.tool_input?.new_string || '';
      if (/\.venv/.test(content)) {
        deny('Never use .venv/bin/python in plists — breaks on uv Python upgrades. Use uv run --script --python 3.13 instead.');
      }
      // uv run --script without --python falls back to system Python 3.9
      if (/uv/.test(content) && /--script/.test(content) && !/--python/.test(content)) {
        deny('uv run --script in plist without --python will fall back to system Python 3.9. Add --python 3.13.');
      }
    }

    // Block npx in hook files — hooks must use direct paths, not npx fallbacks
    if (/\/\.claude\/hooks\//.test(filePath)) {
      const content = data.tool_input?.content || data.tool_input?.new_string || '';
      if (/\bnpx\b/.test(content)) {
        deny('Never use npx in hooks — unreliable fallback. Use direct path to the installed binary.');
      }
    }

    // Block time-sensitive facts in ~/CLAUDE.md (rules file must use vault pointers, not facts)
    // Covers symlink path and real path
    const isMainClaudeMd = filePath === '~//CLAUDE.md'
      || filePath === '~//reticulum/claude/CLAUDE.md';
    if (isMainClaudeMd) {
      const newContent = data.tool_input?.new_string || data.tool_input?.content || '';
      const factPatterns = [
        { re: /20\d\d-\d{2}-\d{2}/, label: 'ISO date' },
        { re: /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d\d\b/i, label: 'calendar date with year' },
        { re: /HK\$\d+/, label: 'HK dollar amount' },
      ];
      const hits = factPatterns.filter(p => p.re.test(newContent)).map(p => p.label);
      if (hits.length > 0) {
        deny(`CLAUDE.md must not contain time-sensitive facts (${hits.join(', ')} detected). Use a vault pointer instead — e.g. "See [[Capco Transition]]".`);
      }
    }

    // Block checked items being left in Praxis.md — must be moved to archive
    if (/\/notes\/Praxis\.md$/.test(filePath)) {
      const content = data.tool_input?.content || data.tool_input?.new_string || '';
      if (/^- \[x\]/m.test(content)) {
        deny('BLOCKED: Your edit contains "- [x]" checked items. REMOVE them from Praxis.md and APPEND them to ~/notes/Praxis Archive.md in a SEPARATE edit. Do both edits now.');
      }
    }

    // Block writes to past daily notes (immutable historical records)
    // Only applies to write tools — reads are always allowed
    const writeTool = ['Write', 'Edit', 'MultiEdit'].includes(data.tool_name);
    const dailyMatch = filePath.match(/\/notes\/Daily\/(\d{4}-\d{2}-\d{2})\.md$/);
    if (writeTool && dailyMatch) {
      const noteDate = dailyMatch[1];
      const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Hong_Kong' });
      if (noteDate !== today) {
        deny(`Past daily note ${noteDate} is an immutable record. Only today's note (${today}) can be edited.`);
      }
    }

    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
});
