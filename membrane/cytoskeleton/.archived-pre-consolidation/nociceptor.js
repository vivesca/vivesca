#!/usr/bin/env node
/**
 * PreToolUse Hook - Bash command guard
 *
 * Enforces HARD rules by blocking dangerous commands before execution.
 * Uses JSON hookSpecificOutput with permissionDecision: "deny".
 *
 * Guards:
 * 1. rm -r/-rf/--recursive without safe_rm.py
 * 2. tccutil reset (breaks Screen Recording permanently)
 * 3. grep/rg/find targeting home directory without a subdirectory
 * 4. Credential exfiltration (.secrets, keychain, env vars)
 * 5. wacli messages list without --chat flag
 * 6. Session JSONL parsing (use resurface instead)
 * 7. npm in pnpm projects (enforce pnpm preference)
 * 8. uv tool install --force without --reinstall
 * 9. pip install without uv (enforce uv preference)
 * 10. gh gist create --public (enforce secret gists)
 * 11. wacli send (never send WhatsApp directly)
 * 12. git push --force to main/master
 * 13. gog send/reply/forward (draft first, never send directly)
 * 14. bird tweet/post/reply/dm send (draft first, never post directly)
 * 15. Network exfil: curl POST/data, wget --post, scp/rsync remote, nc/netcat
 * 16. Secrets in command args (API keys, tokens, private keys)
 * 17. agent-browser on localhost/financial sites/credentials in URL
 * 18. rm on ~/notes/*.md (use trash, never delete vault notes)
 * 19. curl | bash (pipe-to-shell security risk)
 * 20. git reset --hard / git clean -xfd / git checkout -- . (destructive working tree)
 * 21. Lazy commit messages (one-word throwaway: fix, update, wip, changes, test)
 * 22. sed -i on files (use Edit tool instead)
 */

const fs = require('fs');
const path = require('path');

function logDeny(hookName, reason) {
  try {
    const entry = JSON.stringify({ ts: new Date().toISOString(), hook: hookName, rule: reason.slice(0, 80) }) + '\n';
    fs.appendFileSync('~//logs/hook-fire-log.jsonl', entry);
  } catch (_) {}
}

function deny(reason) {
  logDeny('bash-guard', reason);
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
    const cmd = data.tool_input?.command || '';
    const runInBackground = data.tool_input?.run_in_background === true;

    // 24. Double-backgrounding: run_in_background:true + shell & = orphaned process
    // Catches trailing & and mid-command & (e.g. cmd & \n echo ...), excludes && and &>
    if (runInBackground && /(?<![&])\&(?![&>])\s*(\n|$)/m.test(cmd)) {
      deny('Double-backgrounding detected: `run_in_background: true` already backgrounds the process. Remove the `&` — it orphans the process and the task shows "completed" with no output.');
    }

    // 1. Recursive rm — use deleo
    if (/\brm\b/.test(cmd) && (/\s-\w*r/.test(cmd) || /--recursive/.test(cmd)) && !cmd.includes('safe_rm.py') && !cmd.includes('deleo')) {
      deny('Run `deleo <path>` instead of rm -r. It validates and prompts before deleting.');
    }

    // 2. tccutil reset — never allowed
    if (/\btccutil\s+reset\b/.test(cmd)) {
      deny('tccutil reset breaks Screen Recording permissions permanently.');
    }

    // 3. grep/rg/find on unscoped home directory
    if (/\b(grep|rg|find)\b/.test(cmd)) {
      const padded = ' ' + cmd;
      const homePatterns = [
        /\s~(\s|$)/,                    // ~
        /\s~\/(\s|$)/,                  // ~/
        /\s\/Users\/terry(\s|$)/,       // ~/
        /\s\/Users\/terry\/(\s|$)/,     // ~//
        /\s\$HOME(\s|$)/,               // $HOME
        /\s\$HOME\/(\s|$)/,             // $HOME/
      ];

      if (homePatterns.some(p => p.test(padded))) {
        deny('Never run grep/rg/find on the entire home directory. Scope to a subdirectory.');
      }
    }

    // 4. Credential exfiltration — block direct reads of secrets files and keychain
    if (/\bcat\b.*\.secrets\b/.test(cmd) || /\bless\b.*\.secrets\b/.test(cmd) || /\bhead\b.*\.secrets\b/.test(cmd) || /\btail\b.*\.secrets\b/.test(cmd)) {
      deny('Direct read of .secrets blocked. Credentials are in macOS Keychain.');
    }
    if (/\bsecurity\s+find-generic-password\b/.test(cmd)) {
      deny('Direct Keychain access blocked. Tools fetch their own credentials.');
    }
    if (/\bprintenv\b|\benv\b/.test(cmd) && /(KEY|TOKEN|SECRET|PASSWORD)/.test(cmd)) {
      deny('Credential env var inspection blocked.');
    }

    // 5. wacli messages list without --chat flag (positional JID silently ignored, returns all chats)
    if (/\bwacli\s+messages\s+list\b/.test(cmd) && !(/--chat/.test(cmd))) {
      deny('wacli messages list without --chat returns ALL chats. Use: wacli messages list --chat <JID>');
    }

    // 6. Session JSONL parsing — use resurface instead
    if (/\.claude\/projects\//.test(cmd) && /\.jsonl/.test(cmd)) {
      deny('Use `resurface search "query" --deep` instead of hand-parsing session JSONL files.');
    }

    // 7. npm in pnpm projects — enforce pnpm preference
    if (/\bnpm\s+(install|i|ci|run|exec|test|start|build|publish)\b/.test(cmd)) {
      const cwd = data.cwd || process.cwd();
      let dir = cwd;
      while (dir !== path.dirname(dir)) {
        if (fs.existsSync(path.join(dir, 'pnpm-lock.yaml'))) {
          deny('This project uses pnpm. Replace npm with pnpm.');
        }
        dir = path.dirname(dir);
      }
    }

    // 8. uv tool install --force without --reinstall (won't rebuild from source edits)
    if (/\buv\s+tool\s+install\b/.test(cmd) && /--force/.test(cmd) && !/--reinstall/.test(cmd)) {
      deny('`uv tool install --force` doesn\'t rebuild from source edits. Use `--force --reinstall`.');
    }

    // 9. bare pip install (enforce uv)
    if (/\bpip\s+install\b/.test(cmd) && !/\buv\b/.test(cmd) && !/\buvx\b/.test(cmd)) {
      deny('Use `uv pip install` or `uv add` instead of bare `pip install`.');
    }

    // 10. gh gist create --public (all gists must be secret)
    if (/\bgh\s+gist\s+create\b/.test(cmd) && /--public\b/.test(cmd)) {
      deny('NEVER create public gists. Remove --public (gh gist create defaults to secret).');
    }

    // 11. wacli send — never send WhatsApp directly, draft for Terry
    if (/\bwacli\s+(send|messages\s+send)\b/.test(cmd)) {
      deny('Never send WhatsApp directly. Draft the message in a secret gist for Terry to send manually.');
    }

    // 12. git push --force to main/master
    if (/\bgit\s+push\b/.test(cmd) && /(--force\b|-f\b)/.test(cmd) && /\b(main|master)\b/.test(cmd)) {
      deny('Never force-push to main/master. Use a feature branch or ask Terry first.');
    }

    // 13. gog send/reply/forward — never send email directly, draft first
    if (/\bgog\s+(send|reply|forward)\b/.test(cmd)) {
      deny('Never send email directly. Draft in a secret gist for Terry to review and send manually.');
    }

    // 14. bird tweet/post/reply/dm send — never post directly, draft first
    if (/\bbird\s+(tweet|post|reply|retweet|quote)\b/.test(cmd)) {
      deny('Never post to Twitter directly. Draft in a secret gist for Terry to review and post manually.');
    }
    if (/\bbird\s+dm\s+send\b/.test(cmd)) {
      deny('Never send Twitter DMs directly. Draft for Terry to send manually.');
    }

    // 15. Network exfil — block outbound data transfers
    if (/\bcurl\b/.test(cmd) && /(-X\s*(POST|PUT|PATCH)\b|--data\b|-d\s|-F\s|--upload-file\b|-T\s)/.test(cmd)) {
      deny('Outbound POST/upload via curl blocked. Use named tools (gh, gog, bird, pplx) for external communication.');
    }
    if (/\bwget\s+--post/.test(cmd)) {
      deny('Outbound POST via wget blocked. Use named tools for external communication.');
    }
    if (/\b(scp|rsync)\b/.test(cmd) && /:/.test(cmd) && !/localhost/.test(cmd)) {
      deny('Remote file transfer blocked. Ask Terry before sending files to remote hosts.');
    }
    if (/\b(nc|ncat|netcat|socat)\b/.test(cmd) && /\d+\.\d+\.\d+\.\d+/.test(cmd)) {
      deny('Raw socket connections blocked. Use named tools for network communication.');
    }

    // 16. Secrets in command args — detect API keys, tokens, private keys in commands
    if (/\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{22,})\b/.test(cmd)) {
      deny('GitHub token detected in command. Use macOS Keychain or env vars, never inline tokens.');
    }
    if (/\bsk-[a-zA-Z0-9]{20,}\b/.test(cmd)) {
      deny('API key (sk-...) detected in command. Use macOS Keychain or env vars, never inline tokens.');
    }
    if (/\bAKIA[0-9A-Z]{16}\b/.test(cmd)) {
      deny('AWS access key detected in command. Use macOS Keychain or env vars, never inline tokens.');
    }
    if (/\b(xoxb-|xoxp-)[a-zA-Z0-9-]+/.test(cmd)) {
      deny('Slack token detected in command. Use macOS Keychain or env vars, never inline tokens.');
    }
    if (/-----BEGIN\s+(RSA|OPENSSH|EC|PGP)\s+PRIVATE\s+KEY-----/.test(cmd)) {
      deny('Private key detected in command. Never paste private keys into commands.');
    }

    // 17. agent-browser on localhost/financial sites/credentials in URL
    if (/\bagent-browser\b/.test(cmd)) {
      if (/\blocalhost\b|127\.0\.0\.1|0\.0\.0\.0/.test(cmd)) {
        deny('agent-browser on localhost blocked — exposes local services. Use curl for local APIs.');
      }
      if (/[?&](key|token|password|secret|api_key)=/i.test(cmd)) {
        deny('URL contains credentials in query params. Remove secrets from the URL.');
      }
      if (/\b(hsbc|citibank|chase|wellsfargo|paypal|venmo|wise|revolut)\.com\b/i.test(cmd)) {
        deny('agent-browser on financial sites blocked. Use the official site manually for banking.');
      }
    }

    // 18. rm on ~/notes/*.md — vault notes are never deleted
    if (/\brm\b/.test(cmd) && /(~\/notes\/|\/Users\/terry\/notes\/)/.test(cmd) && /\.md\b/.test(cmd)) {
      deny('Never delete Obsidian vault notes. Move to ~/notes/.trash/ or archive instead.');
    }

    // 19. curl | bash — pipe-to-shell is a security risk
    if (/\b(curl|wget)\b.*\|\s*(bash|sh|zsh)\b/.test(cmd)) {
      deny('Piping curl/wget to shell is a security risk. Download the script first, inspect it, then run.');
    }

    // 20. git destructive working tree operations
    if (/\bgit\s+reset\s+--hard\b/.test(cmd)) {
      deny('git reset --hard destroys uncommitted work. Use `git stash` to save changes first, or `git reset --soft`.');
    }
    if (/\bgit\s+clean\b/.test(cmd) && /-[a-z]*f/.test(cmd)) {
      deny('git clean -f permanently deletes untracked files. Use `git clean -n` (dry run) first, then ask Terry.');
    }
    if (/\bgit\s+checkout\s+--\s*\./.test(cmd)) {
      deny('git checkout -- . discards all unstaged changes. Use `git stash` or target specific files.');
    }
    if (/\bgit\s+restore\s+\./.test(cmd) && !(/--staged/.test(cmd))) {
      deny('git restore . discards all unstaged changes. Use `git stash` or target specific files.');
    }

    // 22. gog calendar today — subcommand doesn't exist
    if (/\bgog\s+calendar\s+today\b/.test(cmd)) {
      deny('`gog calendar today` does not exist. Use `gog calendar list` instead.');
    }

    // 23. uv publish — doesn't read ~/.pypirc, use twine
    if (/\buv\s+publish\b/.test(cmd)) {
      deny('`uv publish` does not read ~/.pypirc. Use `uvx twine upload dist/*` instead.');
    }

    // 22. sed -i — use Edit tool instead
    if (/\bsed\s+(-i|--in-place)\b/.test(cmd)) {
      deny('Use the Edit tool instead of `sed -i`. Read the file first, then Edit.');
    }

    // 25. launchctl stop — KeepAlive restarts immediately, use unload
    if (/\blaunchctl\s+stop\b/.test(cmd)) {
      deny('`launchctl stop` is immediately undone by KeepAlive. Use `launchctl unload ~/Library/LaunchAgents/<plist>` to actually disable.');
    }

    // 26. gh repo create without --private — personal repos must be private
    if (/\bgh\s+repo\s+create\b/.test(cmd) && !/--private\b/.test(cmd) && !/--public\b/.test(cmd)) {
      deny('Personal GitHub repos must be private. Add --private to gh repo create.');
    }

    // 27. security add-generic-password without newline strip — trailing \n causes 400 errors
    if (/\bsecurity\s+add-generic-password\b/.test(cmd) && /-w\s+"\$\(/.test(cmd) && !/tr\s+-d/.test(cmd)) {
      deny('`security add-generic-password -w "$(cmd)"` stores a trailing \\n — API calls will return 400. Always strip: `security add-generic-password -w "$(cmd | tr -d \'\\n\')"`');
    }

    // 28. cat/head/tail for reading files — use Read tool instead
    // Allow: pipes (|), heredocs (<<), process substitution, /dev/, echo/printf piped to cat
    if (/\b(cat|head|tail)\b/.test(cmd) && !/\|/.test(cmd) && !/<</.test(cmd) && !/\/dev\//.test(cmd) && !/\b(echo|printf)\b/.test(cmd) && !/>\s/.test(cmd)) {
      deny('Use the Read tool instead of cat/head/tail for reading files. Bash cat/head/tail is only for pipes and heredocs.');
    }

    // 29. grep/rg for searching file contents — use Grep tool instead
    // Allow: pipes (cmd | grep), process substitution, grep on command output
    if (/\b(grep|rg)\b/.test(cmd) && !/\|/.test(cmd) && !/<</.test(cmd) && !/\$\(/.test(cmd) && !/\/dev\//.test(cmd)) {
      deny('Use the Grep tool instead of grep/rg for searching file contents. Bash grep is only for filtering command output via pipes.');
    }

    // 21. Lazy commit messages — one-word throwaways
    const commitMatch = cmd.match(/\bgit\s+commit\b.*-m\s+["']([^"']+)["']/);
    if (commitMatch) {
      const msg = commitMatch[1].trim().toLowerCase();
      const lazy = /^(fix|update|wip|changes|test|stuff|tmp|asdf|todo|misc|cleanup|refactor)$/;
      if (lazy.test(msg)) {
        deny(`Lazy commit message "${commitMatch[1]}" blocked. Write a specific message explaining WHAT changed and WHY.`);
      }
    }

    process.exit(0);
  } catch (err) {
    // Don't block on hook errors
    process.exit(0);
  }
});
