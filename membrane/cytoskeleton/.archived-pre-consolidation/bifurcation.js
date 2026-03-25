#!/usr/bin/env node
/**
 * PreToolUse hook — when launching a delegate (gemini/codex/opencode) via Bash,
 * check if another delegate was launched recently to the same project.
 * If so, nudge toward parallel worktrees instead of sequential.
 *
 * Also nudges on tool diversity — if same tool used 3+ times in a row,
 * suggest routing by task signal (strategos Step 3).
 */

const fs = require("fs");
const path = require("path");

const STATE_FILE = "/tmp/delegate-history.json";
const DELEGATE_RE = /\b(gemini|codex exec|opencode run)\b/i;
const CD_RE = /cd\s+([^\s&;]+)/;

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return { launches: [] };
  }
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

const input = JSON.parse(fs.readFileSync("/dev/stdin", "utf8"));
const command = input.tool_input?.command || "";

if (!DELEGATE_RE.test(command)) process.exit(0);

const toolMatch = command.match(DELEGATE_RE);
const tool = toolMatch[1].toLowerCase().replace(" exec", "");
const cdMatch = command.match(CD_RE);
const project = cdMatch ? cdMatch[1].replace(/^~/, process.env.HOME) : "unknown";

const state = loadState();
const now = Date.now();

// Clean entries older than 30 minutes
state.launches = state.launches.filter((l) => now - l.ts < 30 * 60 * 1000);

// Check for sequential same-project delegates (not in worktrees)
const sameProject = state.launches.filter(
  (l) => l.project === project && now - l.ts < 10 * 60 * 1000
);

if (sameProject.length > 0 && !project.includes(".")) {
  // Not already in a worktree (worktrees have dots like docima.langmem-backend)
  console.log(
    `[parallel-nudge] Sequential delegate to same project detected. ` +
      `Consider lucus worktrees for parallel execution: ` +
      `\`lucus new <branch>\` → launch in isolated worktree.`
  );
}

// Check for tool diversity — 3+ same tool in a row
const recentTools = state.launches.slice(-2).map((l) => l.tool);
if (recentTools.length >= 2 && recentTools.every((t) => t === tool)) {
  console.log(
    `[parallel-nudge] 3rd consecutive ${tool} delegate. ` +
      `Route by signal: Codex for multi-file/Rust, Gemini for algorithmic, OpenCode for boilerplate. ` +
      `See rector Step 3.`
  );
}

// Record this launch
state.launches.push({ tool, project, ts: now });
saveState(state);
