#!/usr/bin/env node
/**
 * PreToolUse Hook - Read tool guard
 *
 * Blocks reading sensitive files (credentials, secrets).
 * Blocks reading lockfiles and binaries (context waste).
 * Mirrors bash-guard rule 4 but for the Read tool.
 */

const fs = require('fs');

function logDeny(hookName, reason) {
  try {
    const entry = JSON.stringify({ ts: new Date().toISOString(), hook: hookName, rule: reason.slice(0, 80) }) + '\n';
    fs.appendFileSync('/Users/terry/logs/hook-fire-log.jsonl', entry);
  } catch (_) {}
}

function deny(reason) {
  logDeny('read-guard', reason);
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

    const sensitivePatterns = [
      /\.secrets$/,
      /\.secrets\.d\//,
      /\.env$/,
      /\.env\.local$/,
      /\.pypirc$/,
      /credentials\.json$/,
    ];

    if (sensitivePatterns.some(p => p.test(filePath))) {
      deny(`Read of sensitive file blocked: ${filePath}. Credentials are in macOS Keychain — tools fetch their own.`);
    }

    // Block reading lockfiles (massive, zero reasoning value)
    const lockfilePatterns = [
      /package-lock\.json$/,
      /pnpm-lock\.yaml$/,
      /yarn\.lock$/,
      /Cargo\.lock$/,
      /poetry\.lock$/,
      /Gemfile\.lock$/,
      /composer\.lock$/,
    ];
    if (lockfilePatterns.some(p => p.test(filePath))) {
      deny(`Reading lockfiles wastes context. Use grep to find specific package versions, or inspect the manifest (package.json, Cargo.toml) instead.`);
    }

    // Block reading minified/binary files (context pollution)
    const binaryPatterns = [
      /\.min\.js$/,
      /\.min\.css$/,
      /\.sqlite$/,
      /\.db$/,
      /\.zip$/,
      /\.tar(\.gz)?$/,
      /\.gz$/,
      /\.dmg$/,
      /\.wasm$/,
    ];
    if (binaryPatterns.some(p => p.test(filePath))) {
      deny(`Reading binary/minified files wastes context. Use specific tools to inspect these formats.`);
    }

    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
});
