Run the test suite for the current subproject. If $ARGUMENTS is provided, use it to filter which tests to run.

Detect the active subproject from the current working directory, then run the appropriate tests.

**open-event-server:**
```
cd open-event-server
poetry run pytest tests/ -v $ARGUMENTS
```
Note: requires PostgreSQL running (start with `docker compose up -d postgres` if needed).

**intellisoft-middleware:**
No automated test suite. Run the manual verification sequence instead:
```
cd intellisoft-middleware
KHSC_API_USERNAME=x KHSC_AUTHORIZATION=x KHSC_PASS_KEY=x KHSC_SECRET_KEY=x \
OPEN_EVENT_ADMIN_EMAIL=x OPEN_EVENT_ADMIN_PASSWORD=x \
.venv/bin/python -c "from app.main import app; print('OK — routes:', [r.path for r in app.routes])"
```
Then run a health check and import smoke test if the stack is running.

**open-event-organizer-android:**
```
cd open-event-organizer-android
./gradlew testDebugUnitTest $ARGUMENTS
```
Coverage report: `app/build/reports/tests/testDebugUnitTest/index.html`

To run a single test class:
```
./gradlew testPlayStoreDebugUnitTest --tests=<ClassName> $ARGUMENTS
```

**open-event-organizer-ios:**
```
cd open-event-organizer-ios
xcodebuild test \
  -workspace EventyayOrganizer.xcworkspace \
  -scheme EventyayOrganizer \
  -destination 'platform=iOS Simulator,name=iPhone 15' $ARGUMENTS
```

**open-event-frontend:**
```
cd open-event-frontend
yarn test $ARGUMENTS
```

After running, report:
- Number of tests passed / failed / skipped
- Any failing test names and the error message
- Suggest fixes based on `.claude/rules/testing.md` if relevant
