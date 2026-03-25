# Epigenome

This is a vivesca epigenome — an instance repo that personalises the universal vivesca organism for one person.

The **genome** (vivesca) encodes structure and behaviour.
The **epigenome** (this repo) expresses it: credentials, config, constitution, and automation.

## Structure

```
epigenome/
  credentials/           API keys and secrets (gitignored, not committed)
    .env.template        List of required vars — copy to .env and populate
  config/
    server.yaml          MCP server host/port
    config.yaml          Instance identity (name, vault path, etc.)
  launchd/               macOS LaunchAgent plists for automation
  genome.md        Your rules and constraints for Claude
  .gitignore
  README.md              This file
```

## Getting started

1. Populate credentials:
   ```
   cp credentials/.env.template credentials/.env
   # Edit credentials/.env with your API keys
   ```

2. Edit `config/config.yaml` — set your name, vault path, etc.

3. Customise `genome.md` with your own rules.

4. Add LaunchAgent plists to `launchd/` for automation.

5. Run `vivesca serve` from the genome repo.
