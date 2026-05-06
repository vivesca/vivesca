#!/usr/bin/env node
/**
 * PreCompact Hook - Auto-flush state before context compaction
 *
 * Before context is summarized:
 * 1. Auto-commits dirty key repos and pushes them
 * 2. Parses transcript for last meaningful user messages
 * 3. Stamps G1.md with compaction time + in-flight context
*/

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const HOME = process.env.HOME;
const NOW_MD = path.join(HOME, 'notes', 'G1.md');

// Auto-commit + push these repos
const AUTO_COMMIT_REPOS = [
  { name: 'reticulum', path: path.join(HOME, 'reticulum') },
  { name: 'skills', path: path.join(HOME, 'skills') },
];

// Patterns that indicate non-human content in transcript
const SKIP_PATTERNS = [
  /^<local-command/,
  /^<command-name>/,
  /^<command-message>/,
  /^<local-command-stdout>/,
  /^<system-reminder>/,
  /^\s*\/[a-z]/,   // slash commands like /exit /compact
];

function isHumanMessage(content) {
  if (typeof content !== 'string') return false;
  const trimmed = content.trim();
  if (!trimmed || trimmed.length < 3) return false;
  return !SKIP_PATTERNS.some(p => p.test(trimmed));
}

function extractLastUserMessages(transcriptPath, n = 4) {
  try {
    if (!transcriptPath || !fs.existsSync(transcriptPath)) return [];
    const lines = fs.readFileSync(transcriptPath, 'utf8').trim().split('\n');
    const messages = [];
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (entry.type !== 'user') continue;
        const content = typeof entry.message?.content === 'string'
          ? entry.message.content
          : entry.message?.content?.[0]?.text ?? '';
        if (isHumanMessage(content)) {
          messages.push(content.trim().slice(0, 120).replace(/\n+/g, ' '));
        }
      } catch { /* skip malformed lines */ }
    }
    return messages.slice(-n);
  } catch {
    return [];
  }
}

function autoCommitAndPush(repo) {
  try {
    const status = execSync(`git -C "${repo.path}" status --porcelain`, {
      encoding: 'utf8', timeout: 5000,
    }).trim();
    if (!status) return null;

    execSync(
      `git -C "${repo.path}" add -A && git -C "${repo.path}" commit -m "chore: pre-compact auto-flush"`,
      { encoding: 'utf8', timeout: 10000 }
    );

    // Push — best-effort, non-fatal if offline
    try {
      execSync(`git -C "${repo.path}" push`, { encoding: 'utf8', timeout: 15000 });
    } catch { /* push failure is non-fatal */ }

    return status.split('\n').length;
  } catch {
    return null;
  }
}

function stampNowMd(recentMessages, trigger) {
  try {
    if (!fs.existsSync(NOW_MD)) return;

    const now = new Date();
    const hkt = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Hong_Kong',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hour12: false,
    }).format(now).replace(',', '');

    const triggerLabel = trigger === 'manual' ? 'manual /compact' : 'auto-compact';
    const lines = [`\n<!-- compacted: ${hkt} HKT (${triggerLabel}) -->`];

    if (recentMessages.length > 0) {
      lines.push('<!-- last messages before compaction:');
      recentMessages.forEach(m => lines.push(`  - "${m}"`));
      lines.push('-->');
    }

    fs.appendFileSync(NOW_MD, lines.join('\n') + '\n');
  } catch { /* non-fatal */ }
}

function main() {
  // Read hook input from stdin
  let input = {};
  try {
    const raw = fs.readFileSync('/dev/stdin', 'utf8').trim();
    if (raw) input = JSON.parse(raw);
  } catch { /* stdin may be empty in manual invocation */ }

  const { transcript_path, trigger = 'auto' } = input;

  const logMessages = [];

  // 1. Auto-commit + push dirty repos
  for (const repo of AUTO_COMMIT_REPOS) {
    const count = autoCommitAndPush(repo);
    if (count !== null) {
      logMessages.push(`auto-committed+pushed ${repo.name} (${count} file${count > 1 ? 's' : ''})`);
    }
  }

  // G1.md stamping removed — anam search --deep recovers context better than 4 truncated snippets

if (logMessages.length > 0) {
    console.error(`[PreCompact] ${logMessages.join('; ')}`);
  }
}

main();
