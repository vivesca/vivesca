# OpenCode Config Resolution

## Model default

Set in **global** config (`~/.config/opencode/opencode.json`), not project-scoped `.opencode/config.json`.

```json
{
  "model": "zai-coding-plan/glm-5-turbo"
}
```

Project config only loads in registered project directories (check `opencode debug scrap`). `~` is not a registered project, so `.opencode/config.json` there won't load.

## Provider disambiguation

- `zai-coding-plan/glm-5-turbo` — works (Z.AI Coding Plan credentials via `ZHIPU_API_KEY`)
- `zhipuai-coding-plan/glm-5-turbo` — auth failure (different credential path)
- `opencode/glm-5` — OpenCode proxy, requires OpenCode Zen auth

Always use `zai-coding-plan/` prefix for Zhipu Coding Plan models.

## Config location

```
~/.config/opencode → ~/officina/opencode  (symlinked, version controlled)
```

Useful commands:
- `opencode models | grep <name>` — list available model IDs
- `opencode providers ls` — show configured providers
- `opencode debug paths` — show config/data/cache paths
- `opencode debug config` — show resolved config (large output)
