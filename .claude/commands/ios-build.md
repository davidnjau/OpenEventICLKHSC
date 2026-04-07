Build, test, or manage the iOS Eventyay Organizer app.

Usage:
- `/ios-build`          → build the app for the simulator
- `/ios-build test`     → run unit tests
- `/ios-build logs`     → stream live simulator logs
- `/ios-build install`  → add new Swift files to the Xcode project target

**Build:**
```bash
cd open-event-organizer-ios
xcodebuild -workspace EventyayOrganizer.xcworkspace \
  -scheme EventyayOrganizer \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro Max' \
  build 2>&1 | grep -E "error:|warning:|BUILD"
```

**Test:**
```bash
cd open-event-organizer-ios
xcodebuild test \
  -workspace EventyayOrganizer.xcworkspace \
  -scheme EventyayOrganizer \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro Max' 2>&1 \
  | grep -E "Test Suite|passed|failed|error:"
```

**Stream simulator logs (for the running app):**
```bash
UDID=$(xcrun simctl list devices | grep "iPhone 16 Pro Max" | grep Booted | grep -oE '[A-F0-9-]{36}')
xcrun simctl spawn "$UDID" log stream \
  --predicate 'processImagePath CONTAINS "EventyayOrganizer"' \
  --level debug --style compact
```

**Add new Swift files to Xcode project target:**
When new `.swift` files are created on disk but not yet in `project.pbxproj`, use the
`ruby /tmp/add_files.rb` approach with the `xcodeproj` gem. See `tools/add_ios_files.rb`
for the reusable script.

**If build fails with "No such module":**
The `.xcworkspace` must be used, not `.xcodeproj`.
```bash
open open-event-organizer-ios/EventyayOrganizer.xcworkspace
```
Then press ⌘R in Xcode.

**Base URL** is `http://<SERVER_HOST>:8080/v1` — set `SERVER_HOST` in the root `.env`
and run `python3 setup.py` to regenerate `LocalConfig.swift`.
