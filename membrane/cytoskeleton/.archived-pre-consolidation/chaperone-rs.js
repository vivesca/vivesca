#!/usr/bin/env node
/**
 * PostToolUse Hook - Auto-format Rust files with rustfmt after Edit/Write
 *
 * Only runs if:
 * - File is .rs
 * - rustfmt is available
 * - File is inside a Cargo project (has Cargo.toml ancestor)
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

    if (!filePath || !/\.rs$/.test(filePath)) {
      console.log(input);
      return;
    }

    // Find Cargo.toml (project root)
    let dir = path.dirname(filePath);
    while (dir !== path.dirname(dir)) {
      if (fs.existsSync(path.join(dir, 'Cargo.toml'))) {
        break;
      }
      dir = path.dirname(dir);
    }

    if (!fs.existsSync(path.join(dir, 'Cargo.toml'))) {
      console.log(input);
      return;
    }

    try {
      execSync(`rustfmt "${filePath}"`, {
        cwd: dir,
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 10000
      });
      console.error(`[PostEdit] Formatted: ${path.basename(filePath)}`);
    } catch (e) {
      // rustfmt not available or failed - silent
    }

    console.log(input);
  } catch (err) {
    console.log(input);
  }
});
