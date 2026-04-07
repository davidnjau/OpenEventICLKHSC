Build, test, or manage the Android Eventyay Organizer app.

Usage:
- `/android-build`         → assemble debug APK
- `/android-build install` → build and install on connected device/emulator
- `/android-build test`    → run unit tests
- `/android-build logs`    → stream logcat from connected device

**Assemble debug APK:**
```bash
cd open-event-organizer-android
./gradlew assemblePlayStoreDebug 2>&1 | tail -20
```
Output: `app/build/outputs/apk/playStore/debug/app-playStore-debug.apk`

**Build and install on emulator:**
```bash
cd open-event-organizer-android
ADB=~/Library/Android/sdk/platform-tools/adb
./gradlew assemblePlayStoreDebug && \
  $ADB install -r app/build/outputs/apk/playStore/debug/app-playStore-debug.apk
```

**Unit tests:**
```bash
cd open-event-organizer-android
./gradlew testDebugUnitTest 2>&1 | grep -E "PASSED|FAILED|ERROR|tests"
```
Single test class: `./gradlew testPlayStoreDebugUnitTest --tests=<ClassName>`

**Stream logcat (app only):**
```bash
ADB=~/Library/Android/sdk/platform-tools/adb
$ADB logcat -c
$ADB logcat | grep -E "eventyay|organizer|Attendee|CheckIn|KHSC" --line-buffered
```

**Common issues:**

| Error | Fix |
|---|---|
| `Cannot deserialize 'long' from String` | `@JsonIgnoreProperties("identifier")` on the model class |
| `Included must be an array` | marshmallow_jsonapi patch missing — check bind mount in `docker-compose.yml` |
| DB schema mismatch on upgrade | Increment `OrgaDatabase.DATABASE_VERSION` and add migration |
| RxJava leak | Dispose in `onDestroy` via `CompositeDisposable` |

**Base URL** is set in `app/build.gradle` via the root `.env` → `SERVER_HOST`.
Run `python3 setup.py` from the repo root to regenerate it.
