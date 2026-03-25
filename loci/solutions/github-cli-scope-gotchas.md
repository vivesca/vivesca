# GitHub CLI Scope Gotchas

## Default scopes aren't enough for profile management

`gh auth login` grants `repo`, `read:org`, `gist`, `workflow` by default. Several common operations need additional scopes:

| Action | Required scope | Command to add |
|--------|---------------|----------------|
| Update bio/location/blog | `user` | `gh auth refresh -h github.com -s user` |
| Delete repos | `delete_repo` | `gh auth refresh -h github.com -s delete_repo` |

## Repo pinning is web-only

There is no GraphQL mutation for pinning repos to a GitHub profile. `addPinnedItem` doesn't exist despite appearing in some docs. Must be done manually at github.com > "Customize your pins".

## `gh repo edit` is silent on success

`gh repo edit --description "..."` and `--add-topic` produce zero output on success. Don't assume failure if you see nothing.
