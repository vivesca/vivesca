#!/usr/bin/env node
/**
 * PostToolUse Hook - TypeScript check after editing .ts/.tsx files
 *
 * Shows type errors for the edited file only (not full project).
 * Silent if tsc not available or no tsconfig.json found.
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

    // Only check TS files
    if (!/\.(ts|tsx)$/.test(filePath)) {
      console.log(input);
      return;
    }

    // Check file exists
    if (!fs.existsSync(filePath)) {
      console.log(input);
      return;
    }

    // Find tsconfig.json
    let dir = path.dirname(filePath);
    while (dir !== path.dirname(dir)) {
      if (fs.existsSync(path.join(dir, 'tsconfig.json'))) {
        break;
      }
      dir = path.dirname(dir);
    }

    if (!fs.existsSync(path.join(dir, 'tsconfig.json'))) {
      console.log(input);
      return;
    }

    // Run tsc --noEmit with incremental caching, filter errors for this file
    const localTsc = path.join(dir, 'node_modules', '.bin', 'tsc');
    const tscBin = fs.existsSync(localTsc) ? `"${localTsc}"` : 'npx tsc';
    try {
      const result = execSync(`${tscBin} --noEmit --incremental --pretty false 2>&1`, {
        cwd: dir,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 30000
      });
      // No errors
    } catch (e) {
      const output = e.stdout || '';
      const errors = output.split('\n')
        .filter(line => line.includes(filePath) || line.includes(path.basename(filePath)))
        .slice(0, 5);

      if (errors.length > 0) {
        console.error('[TypeCheck] Errors in ' + path.basename(filePath) + ':');
        errors.forEach(err => console.error(err));
      }
    }

    console.log(input);
  } catch (err) {
    console.log(input);
  }
});
