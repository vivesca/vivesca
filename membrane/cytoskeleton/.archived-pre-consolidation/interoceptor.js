#!/usr/bin/env node
/**
 * Notification Hook - Log background task completions
 *
 * Logs notifications to a file so background task results
 * aren't silently lost if the agent misses them.
 */

const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(process.env.HOME, 'logs', 'notification-log.jsonl');

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const now = new Date().toISOString();

    const entry = JSON.stringify({
      timestamp: now,
      type: data.type || 'unknown',
      message: data.message || '',
      tool: data.tool_name || '',
    });

    // Ensure log directory exists
    const logDir = path.dirname(LOG_FILE);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    fs.appendFileSync(LOG_FILE, entry + '\n');
  } catch {
    // Don't block on errors
  }
  process.exit(0);
});
