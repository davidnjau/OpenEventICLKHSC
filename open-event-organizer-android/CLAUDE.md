# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
./gradlew assembleDebug                  # Build debug APK
./gradlew assembleFdroidRelease          # Build F-Droid release APK
./gradlew assemblePlayStoreRelease       # Build Play Store release APK
./gradlew clean                          # Clean build outputs
```

## Test Commands

```bash
./gradlew test                           # Run all unit tests
./gradlew testDebugUnitTest             # Run debug unit tests
./gradlew testPlayStoreReleaseUnitTestCoverage  # Run with JaCoCo coverage report
./gradlew connectedAndroidTest          # Run instrumented tests (requires device/emulator)

# Run a single test class
./gradlew testPlayStoreDebugUnitTest --tests=com.eventyay.organizer.core.track.update.UpdateTrackViewModelTest
```

Unit tests use Robolectric and do not require a device. Coverage reports are generated in `build/reports/jacoco/`.

JaCoCo excludes generated code from coverage (Dagger, DBFlow, R.class, databinding).

## Lint & Formatting

```bash
./gradlew spotlessCheck                  # Check code formatting
./gradlew spotlessApply                  # Auto-fix formatting issues
./gradlew lint                           # Run Android lint
```

Spotless enforces 2-space indentation, removes unused imports, trims trailing whitespace, and ends files with newlines. It auto-applies before each build.

## Architecture: MVP + MVVM (in transition)

The project uses **MVP (Model-View-Presenter)** for older feature modules and is transitioning to **MVVM (ViewModel + LiveData)** for newer ones. Both patterns coexist under `com.eventyay.organizer`. Prefer MVVM (`ViewModel` + `LiveData`) for new features.

### Layer Responsibilities

**View (Fragment/Activity):** Passive display only. Each feature has a `*View` interface implemented by a Fragment/Activity. Base classes: `BaseFragment`, `BaseActivity`. Trait interfaces (`Progressive`, `Successful`, `Erroneous`, `Refreshable`, `Emptiable`) are mixed in as needed.

**Presenter (MVP):** All business logic lives here. Zero Android dependencies — fully unit-testable with Mockito/Robolectric. Manages RxJava subscriptions and view lifecycle. Base classes: `BasePresenter`, `AbstractBasePresenter`.

**ViewModel (MVVM):** Newer modules use `androidx.lifecycle.ViewModel`. One-time UI events use `SingleEventLiveData`. Observe in Fragments via `LiveData`.

**Repository (Data Layer):** Orchestrates network (Retrofit) and local database (DBFlow). Uses a `reload` flag to bypass cache. Rate limiting (`RateLimiter<String>`) prevents redundant network requests (10-minute windows by default). Disk and network observables are composed with `AbstractObservable.AbstractObservableBuilder`. Each feature has a corresponding repository interface + `RepositoryImpl` (e.g., `AttendeeRepository`, `EventRepository`).

### Key Packages

- `common/di/` — Dagger 2 modules and component graph
- `common/mvp/` — Base MVP classes and view trait interfaces
- `core/` — Feature modules (auth, event, attendee, orders, ticket, session, speaker, etc.)
- `data/` — Repositories, DBFlow database models, Retrofit API definitions
- `ui/binding/` — Custom DataBinding adapters
- `utils/service/` — Background services

### Dependency Injection

Uses **Dagger 2** with constructor injection as the preferred style. `AppModule` aggregates `AndroidModule`, `RepoModule`, `ModelModule`, `NetworkModule`, and `ViewModelModule`. Repositories are bound with `@Binds` at `@Singleton` scope. ViewModels use `@IntoMap` + `@ViewModelKey` for factory injection. A `FlavorModule` (abstract, duplicated in `src/fdroid/` and `src/playStore/`) provides flavor-specific implementations (e.g., barcode scanning). Activities use `@ContributesAndroidInjector` with nested Fragment builder declarations.

### Reactive Programming

**RxJava 2** throughout — network requests return Observables, repository methods compose streams. Presenters manage subscription lifecycle (dispose on view detach). RxAndroid provides the main thread scheduler.

Unit tests must override schedulers to avoid async behavior. Standard setup:

```java
@Before
public void setUp() {
    RxJavaPlugins.setIoSchedulerHandler(scheduler -> Schedulers.trampoline());
    RxAndroidPlugins.setInitMainThreadSchedulerHandler(schedulerCallable -> Schedulers.trampoline());
}

@After
public void tearDown() {
    RxJavaPlugins.reset();
    RxAndroidPlugins.reset();
}
```

ViewModel tests additionally need `@Rule InstantTaskExecutorRule` for LiveData.

## Product Flavors

- **`playStore`** — Uses Google Vision API and Places API for barcode/QR scanning
- **`fdroid`** — Uses QRCodeScanner library instead (no Google dependencies)

Flavor-specific code goes in `src/playStore/java/` or `src/fdroid/java/`. The `FlavorModule` (Dagger) is the primary injection point for swapping flavor implementations.

API endpoints:
- Debug: `http://192.168.100.125:8080/v1/`
- Release: `https://api.eventyay.com/v1/`

## Key Dependencies

| Category | Library |
|----------|---------|
| DI | Dagger 2 (2.21) |
| Networking | Retrofit 2.3.0, OkHttp 3.10.0 |
| JSON | Jackson, jsonapi-converter 0.10 |
| Reactive | RxJava 2.1.10, RxAndroid 2.1.1 |
| Database | DBFlow 4.1.2 |
| Images | Glide 4.8.0 |
| View Binding | ButterKnife 10.1.0 |
| Code Generation | Lombok 1.16.18 |
| Testing | JUnit 4, Mockito 3.6.0, Robolectric 4.2, Espresso 3.3.0 |

## SDK & Java Requirements

- Min SDK: 21, Target SDK: 28, Compile SDK: 28
- Java: Oracle JDK 8
- Gradle 7.0.2

## CI/CD

- **CircleCI** (primary): Runs `spotlessJavaCheck`, lint, unit tests, and coverage on every push
- **Travis CI** (secondary): Builds both flavors and publishes APKs to the `apk` branch on `development`/`master`

**IMPORTANT:** Every merge to `master` auto-publishes to Google Play as an Alpha release. You **must** increment `versionCode` (integer) and update `versionName` (semver) in `app/build.gradle` before merging to `master`.

## Optional Environment Variables

- `MAPBOX_ACCESS_TOKEN` — Required for map features
- `STORE_PASS`, `ALIAS`, `KEY_PASS` — Signing credentials (CI/CD only)
