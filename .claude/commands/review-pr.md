Review the current branch's changes against main as a pull request review.

Steps:

1. Show what branch we are on and how many commits ahead of main:
   ```
   git branch --show-current
   git log --oneline main..HEAD
   ```

2. Show the full diff stat:
   ```
   git diff main...HEAD --stat
   ```

3. For each changed file, review it for:
   - **Correctness** — does the logic match what the commit says it does?
   - **Security** — no hardcoded credentials, no SQL injection, no XSS
   - **Code style** — follows `.claude/rules/code-style.md` for the relevant language
   - **Breaking changes** — does it change a JSON:API field name, DB column, or API endpoint shape that would break Android, iOS, or the middleware?
   - **Missing tests** — does a logic change have a corresponding test?

4. Cross-stack impact check:
   - If `app/api/` (server schemas) changed → flag Android `Attendee.java`, iOS models, middleware `compare.py`
   - If `intellisoft-middleware/app/` changed → flag KHSC client, scheduler, compare fields
   - If iOS Swift files changed → flag SwiftLint compliance
   - If Android Java/Kotlin files changed → flag DBFlow migration version, RxJava disposal

5. Output a structured review:
   ```
   ## Summary
   <what the PR does>

   ## Issues
   - [ ] <file>:<line> — <issue description>

   ## Suggestions
   - <non-blocking improvements>

   ## Verdict
   APPROVE / REQUEST CHANGES / COMMENT
   ```

If $ARGUMENTS is a PR number (e.g. `42`), fetch it with `gh pr view $ARGUMENTS --json files,body,title`.
