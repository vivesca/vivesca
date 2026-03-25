#!/usr/bin/env node
/**
 * PostToolUse Hook - Auto-format JS/TS files with Prettier after Edit
 *
 * Only runs if:
 * - File is .js/.jsx/.ts/.tsx
 * - prettier is available in the project
 * - Not in ~/notes (vault files)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = data.tool_input?.file_path;

    if (!filePath) {
      console.log(input);
      return;
    }

    // Skip vault files
    if (filePath.includes('/notes/')) {
      console.log(input);
      return;
    }

    // Only format JS/TS files
    if (!/\.(js|jsx|ts|tsx)$/.test(filePath)) {
      console.log(input);
      return;
    }

    // Check file exists
    if (!fs.existsSync(filePath)) {
      console.log(input);
      return;
    }

    // Find project root (has package.json)
    let dir = path.dirname(filePath);
    while (dir !== path.dirname(dir)) {
      if (fs.existsSync(path.join(dir, 'package.json'))) {
        break;
      }
      dir = path.dirname(dir);
    }

    // Format with prettier (local binary only — skip if not installed)
    const localPrettier = path.join(dir, 'node_modules', '.bin', 'prettier');
    if (!fs.existsSync(localPrettier)) {
      console.log(input);
      return;
    }
    try {
      const cmd = `"${localPrettier}" --write "${filePath}"`;
      execSync(cmd, {
        cwd: dir,
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 10000
      });
      console.error(`[PostEdit] Formatted: ${path.basename(filePath)}`);
    } catch (e) {
      // prettier not available or failed - silent
    }

    console.log(input);
  } catch (err) {
    console.log(input);
  }
});
