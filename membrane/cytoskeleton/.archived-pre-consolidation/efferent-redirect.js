#!/usr/bin/env node
// PreToolUse hook: block substantial in-session code writes in ~/code/.
// Soft warn for small edits (≤20 lines), hard block for larger ones.
// Matcher: (tool == 'Edit' || tool == 'Write') && tool_input.file_path matches '/code/'
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(Buffer.concat(chunks).toString());
    const filePath = (input.tool_input || {}).file_path || '';

    if (!/\/Users\/terry\/code\//.test(filePath)) {
      process.exit(0);
      return;
    }

    // Exempt non-code files (markdown, toml, gitignore, lock files)
    if (/\.(md|toml|lock|gitignore|txt|json|yaml|yml)$/.test(filePath)) {
      process.exit(0);
      return;
    }

    // Count lines being written/changed
    const tool = input.tool || '';
    let lineCount = 0;

    if (tool === 'Write') {
      const content = (input.tool_input || {}).content || '';
      lineCount = content.split('\n').length;
    } else if (tool === 'Edit') {
      const newStr = (input.tool_input || {}).new_string || '';
      const oldStr = (input.tool_input || {}).old_string || '';
      // Net new lines added
      lineCount = Math.max(0, newStr.split('\n').length - oldStr.split('\n').length);
      // Also count if the new_string itself is large (even if replacing similar size)
      lineCount = Math.max(lineCount, newStr.split('\n').length);
    }

    if (lineCount > 20) {
      // Hard block — force delegation
      process.stderr.write(
        `DELEGATE GATE: Writing ${lineCount} lines of code in ~/code/ in-session. ` +
        `Delegate to Codex/Gemini/OpenCode instead. ` +
        `Only write in-session if: (1) delegate failed 3+ times, (2) vault context needed, ` +
        `(3) live user decisions required mid-implementation. ` +
        `For edits ≤20 lines (path fix, config tweak, timeout bump): proceed.\n`
      );
      process.exit(1);
    } else {
      // Soft warn for small edits
      process.stdout.write(
        `[delegate-note] Small edit (${lineCount} lines) in ~/code/ — OK for tweaks. ` +
        `For substantial implementation, delegate.\n`
      );
      process.exit(0);
    }
  } catch (_) {
    process.exit(0);
  }
});
