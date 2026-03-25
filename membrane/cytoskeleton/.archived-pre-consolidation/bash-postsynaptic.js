#!/usr/bin/env node
/**
 * PostToolUse Bash dispatcher — single stdin parse, multiple response pathways.
 *
 * Consolidates: exocytosis-nudge (push reminder), auxotrophy (dep pollution),
 * cytokinesis (post-merge checklist), nociception-log (CLI friction logger).
 *
 * Bio: postsynaptic = downstream responses after a neuron (bash) fires.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const FRICTION_LOG = path.join(process.env.HOME, '.claude', 'cli-friction.jsonl');

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const cmd = data.tool_input?.command || '';
    const result = data.tool_output || data.tool_result || '';

    // --- Exocytosis: push reminder after git commit ---
    if (/\bgit\s+commit\b/.test(cmd)) {
      try {
        const cwd = data.cwd || process.cwd();
        const unpushed = execSync(
          `git -C "${cwd}" log --oneline @{upstream}..HEAD 2>/dev/null | wc -l`,
          { encoding: 'utf8', timeout: 5000 }
        ).trim();
        const count = parseInt(unpushed, 10);
        if (count >= 3) {
          process.stderr.write(`${count} unpushed commits in this repo. Consider pushing.\n`);
        }
      } catch { /* non-fatal */ }
    }

    // --- Auxotrophy: dep pollution after delegate invocation ---
    if (/\b(gemini|codex exec|opencode run)\b/i.test(cmd)) {
      try {
        const cdMatch = cmd.match(/cd\s+([^\s&;]+)/);
        if (cdMatch) {
          const projectDir = cdMatch[1].replace(/^~/, process.env.HOME);
          const pyproject = path.join(projectDir, 'pyproject.toml');
          if (fs.existsSync(pyproject)) {
            const content = fs.readFileSync(pyproject, 'utf8');
            const mainDepsMatch = content.match(/\[project\]\s*[\s\S]*?dependencies\s*=\s*\[([\s\S]*?)\]/);
            const optMatch = content.match(/\[project\.optional-dependencies\]([\s\S]*?)(?:\n\[|\n$)/);
            if (mainDepsMatch && optMatch) {
              const mainDeps = mainDepsMatch[1].toLowerCase();
              const optPackages = [];
              const lineRe = /^\w+\s*=\s*\[(.*?)\]/gm;
              let m;
              while ((m = lineRe.exec(optMatch[1])) !== null) {
                const pkgs = m[1].match(/"([^"]+)"/g);
                if (pkgs) pkgs.forEach(p => {
                  optPackages.push(p.replace(/"/g, '').split(/[\[>=<]/)[0].trim().toLowerCase());
                });
              }
              const polluted = optPackages.filter(pkg => mainDeps.includes(`"${pkg}`));
              if (polluted.length > 0) {
                console.log(
                  `[auxotrophy] Dependency pollution in ${pyproject}: ${polluted.join(', ')}. ` +
                  `Remove from [project].dependencies, keep in [project.optional-dependencies].`
                );
              }
            }
          }
        }
      } catch { /* non-fatal */ }
    }

    // --- Cytokinesis: post-merge checklist ---
    if (/\b(lucus merge|git merge)\b/.test(cmd)) {
      const branchMatch = cmd.match(/(?:lucus merge|git merge)\s+([^\s;&#]+)/);
      const branch = branchMatch ? branchMatch[1] : 'delegate branch';
      console.log(
        `[cytokinesis] "${branch}" merged. Verify:\n` +
        `  1. git diff --stat — scope clean?\n` +
        `  2. pyproject.toml — deps unpolluted?\n` +
        `  3. uv run pytest tests/ -v\n` +
        `  4. lucus clean`
      );
    }

    // --- Nociception log: CLI friction ---
    if (result.includes('Exit code') || result.includes('error:')) {
      const personalCli = /~\/bin\/|\/Users\/\w+\/bin\/|\.cargo\/bin\/|moneo|fasti|poros|keryx|deltos|caelum|cerno|stips|adytum|sopor|sarcio|amicus|speculor|legatus|consilium|auceps|qianli|iter|lucus|deleo/;
      if (personalCli.test(cmd)) {
        const cliMatch = cmd.match(/(?:~\/bin\/|\/Users\/\w+\/bin\/|\.cargo\/bin\/)?(\w[\w-]*)/);
        const entry = {
          ts: new Date().toISOString(),
          cli: cliMatch ? cliMatch[1] : 'unknown',
          command: cmd.slice(0, 500),
          error: (typeof result === 'string' ? result : JSON.stringify(result)).slice(0, 500),
        };
        try {
          fs.appendFileSync(FRICTION_LOG, JSON.stringify(entry) + '\n');
        } catch { /* non-fatal */ }
      }
    }

  } catch { /* never crash */ }
  process.exit(0);
});
