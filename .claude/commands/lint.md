Run the linter for the current subproject. Detect which subproject is active based on the current working directory or files open, then run the appropriate linter.

Detection rules:
- If in `open-event-server/` or editing `.py` files from that folder → run flake8 / pylint
- If in `intellisoft-middleware/` → run flake8
- If in `open-event-organizer-android/` → run `./gradlew lint`
- If in `open-event-organizer-ios/` → run `swiftlint lint`
- If in `open-event-frontend/` → run `yarn lint`

**Python (server or middleware):**
```
cd <subproject>
.venv/bin/flake8 app/ --max-line-length=100 --exclude=.venv
```

**Android:**
```
cd open-event-organizer-android
./gradlew lint
# Report is at app/build/reports/lint-results-debug.html
```

**iOS:**
```
cd open-event-organizer-ios
swiftlint lint --path EventyayOrganizer/
```

**Frontend:**
```
cd open-event-frontend
yarn lint
```

Display a summary of errors and warnings. If there are errors, list the files and line numbers.
Suggest fixes for common issues based on the rules in `.claude/rules/code-style.md`.
