# Docker credsStore blocks non-interactive pulls

## Problem

`docker pull` hangs indefinitely when `~/.docker/config.json` has `"credsStore": "osxkeychain"` and the pull runs in a non-interactive context (e.g., Claude Code Bash tool, scripts, CI).

The osxkeychain helper tries to prompt for credentials interactively and blocks when there's no TTY.

## Fix

Temporarily remove `credsStore` (and `plugins` which also reference hooks) from `~/.docker/config.json`:

```json
{
  "auths": {
    "registry.hf.space": {}
  },
  "currentContext": "orbstack"
}
```

Pull the image, then restore the original config. Back up first: `cp ~/.docker/config.json ~/.docker/config.json.bak`

## Notes

- Only affects public image pulls in non-interactive contexts
- OrbStack as Docker runtime works fine otherwise
- The `plugins` section (debug, scout) adds hooks that can also slow things down
