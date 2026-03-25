#!/usr/bin/env node
/**
 * PostToolUse Hook — Stuck/Loop Detection
 *
 * Inspired by OpenHands' StuckDetector. Tracks recent tool calls and warns
 * (via stderr injection into conversation) when repetitive patterns emerge.
 *
 * Patterns detected:
 * 1. Same tool + same args repeated N times (default: 3)
 * 2. Same tool + error result repeated N times (default: 2)
 * 3. Alternating A-B-A-B pattern (default: 6 steps / 3 cycles)
 *
 * State: append-only JSONL at ~/.claude/tool-call-log.jsonl
 * Cleared on each new session (UserPromptSubmit can reset, or auto-cleared
 * when file exceeds 200 entries).
 *
 * This is PostToolUse (read-only). Cannot deny — only warns via stderr.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_PATH = path.join(os.homedir(), '.claude', 'tool-call-log.jsonl');
const MAX_ENTRIES = 200;
const WINDOW = 20; // only look at last N entries for pattern detection

// Thresholds (from OpenHands, tuned for Claude Code)
const SAME_CALL_THRESHOLD = 3;     // same tool + same args
const SAME_ERROR_THRESHOLD = 2;    // same tool + error
const ALTERNATING_STEPS = 6;       // A-B-A-B-A-B = 6 steps

function warn(message) {
  // stderr is injected into the conversation as a system note
  console.error(`[stuck-detector] ${message}`);
}

function hashCall(entry) {
  return `${entry.tool}::${JSON.stringify(entry.args)}`;
}

function readRecentEntries() {
  if (!fs.existsSync(LOG_PATH)) return [];
  try {
    const lines = fs.readFileSync(LOG_PATH, 'utf-8').split('\n').filter(l => l.trim());
    const entries = [];
    for (const line of lines) {
      try {
        entries.push(JSON.parse(line));
      } catch { /* skip malformed */ }
    }
    return entries.slice(-WINDOW);
  } catch {
    return [];
  }
}

function appendEntry(entry) {
  // Auto-clear if file is too large
  if (fs.existsSync(LOG_PATH)) {
    try {
      const lineCount = fs.readFileSync(LOG_PATH, 'utf-8').split('\n').filter(l => l.trim()).length;
      if (lineCount >= MAX_ENTRIES) {
        fs.writeFileSync(LOG_PATH, '');
      }
    } catch { /* ignore */ }
  }
  fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + '\n');
}

function detectPatterns(entries, current) {
  const all = [...entries, current];
  const warnings = [];

  // 1. Same tool + same args repeated
  const currentHash = hashCall(current);
  let repeatCount = 0;
  for (let i = all.length - 1; i >= 0; i--) {
    if (hashCall(all[i]) === currentHash) {
      repeatCount++;
    } else {
      break;
    }
  }
  if (repeatCount >= SAME_CALL_THRESHOLD) {
    warnings.push(
      `Same ${current.tool} call repeated ${repeatCount}x with identical args. ` +
      `Consider: (1) different approach, (2) /compact and rethink, (3) proceed with what you have.`
    );
  }

  // 2. Same tool + error result repeated
  if (current.hasError) {
    let errorRepeat = 0;
    for (let i = all.length - 1; i >= 0; i--) {
      if (all[i].tool === current.tool && all[i].hasError) {
        errorRepeat++;
      } else {
        break;
      }
    }
    if (errorRepeat >= SAME_ERROR_THRESHOLD) {
      warnings.push(
        `${current.tool} has errored ${errorRepeat}x consecutively. ` +
        `Stop and reassess — the same approach won't work. Try a fundamentally different method.`
      );
    }
  }

  // 3. Alternating A-B-A-B pattern
  if (all.length >= ALTERNATING_STEPS) {
    const tail = all.slice(-ALTERNATING_STEPS);
    const hashes = tail.map(hashCall);
    // Check if it's two alternating hashes
    const uniqueHashes = [...new Set(hashes)];
    if (uniqueHashes.length === 2) {
      let isAlternating = true;
      for (let i = 0; i < hashes.length - 2; i++) {
        if (hashes[i] !== hashes[i + 2]) {
          isAlternating = false;
          break;
        }
      }
      if (isAlternating) {
        warnings.push(
          `Detected alternating loop: ${tail[0].tool} ↔ ${tail[1].tool} for ${ALTERNATING_STEPS} steps. ` +
          `This pattern won't converge. Break out with a different strategy or /compact.`
        );
      }
    }
  }

  return warnings;
}

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);

    const tool = data.tool_name || data.tool || 'unknown';
    const args = data.tool_input || {};
    const result = data.tool_output || data.tool_result || '';
    const hasError = typeof result === 'string' && (
      result.toLowerCase().includes('error') ||
      result.toLowerCase().includes('failed') ||
      result.startsWith('Exit code')
    );

    const entry = {
      ts: new Date().toISOString(),
      tool,
      args: typeof args === 'object' ? args : {},
      hasError,
    };

    const recent = readRecentEntries();
    const warnings = detectPatterns(recent, entry);

    // Log the call
    appendEntry(entry);

    // Emit warnings
    for (const w of warnings) {
      warn(w);
    }
  } catch (err) {
    // Never crash — hook errors should not block the session
  }
  process.exit(0);
});
