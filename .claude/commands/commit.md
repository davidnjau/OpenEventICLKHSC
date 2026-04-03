Stage and commit changes following the project commit conventions from `.claude/rules/code-style.md`.

Steps:

1. Run `git status` and `git diff --stat` to see what has changed.

2. If $ARGUMENTS is provided, use it as the commit message directly (skip step 3).

3. Otherwise, analyse the changes and draft a commit message following this format:
   ```
   <type>: <short summary in present tense, under 72 chars, no period>
   ```
   Valid types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`

   Examples:
   - `feat: add /events endpoint with date filtering`
   - `fix: use None instead of empty string for missing KHSC fields`
   - `chore: update .gitignore to exclude hprof files`

4. Show the proposed commit message and the list of files to be staged. Ask for confirmation before committing.

5. Stage all changed tracked files (`git add -u`) plus any new files that are clearly part of the change.
   Do NOT stage: `.env`, `*.hprof`, `__pycache__`, `.claude/rules/`, `.claude/settings.local.json`

6. Commit with the confirmed message.

7. Ask if the user wants to push to origin main.
