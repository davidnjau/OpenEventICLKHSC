# Git Workflow

## Branch strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, always deployable |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `chore/<name>` | Non-functional changes (deps, config) |

Never commit directly to `main` for significant changes — use a feature branch and PR.

## Commit message format

```
<type>: <short summary in present tense, under 72 chars>
```

Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`

- No period at the end
- Imperative mood: "add", "fix", "update" — not "added", "fixed"
- Include `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` when Claude wrote the code

## What NOT to commit

- `.env` files (any environment — dev, staging, prod)
- `*.hprof` heap dumps
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `Pods/` (iOS)
- `.gradle/` build caches
- Any file containing production credentials

## Before pushing

1. `git diff --stat` — confirm you know what changed
2. Check no `.env` or secret file is staged: `git status`
3. Run the relevant linter: `/lint`
4. For Open Event server changes: run `poetry run pytest tests/ -v` first

## Author identity

Always commit as **David Maina Njau** (`davidnjau21@gmail.com`).
If `git config user.name` is wrong, set it:
```bash
git config user.name "David Maina Njau"
git config user.email "davidnjau21@gmail.com"
```
