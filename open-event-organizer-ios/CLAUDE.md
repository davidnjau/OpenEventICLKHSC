# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

iOS organiser app for Open Event — mirrors the Android app's feature set. Built with Swift, targeting iOS 12+. Uses **CocoaPods** for dependency management and communicates with the Open Event server via JSON:API.

## Setup

```bash
# Install dependencies (requires CocoaPods)
pod install

# Open the workspace (NOT the .xcodeproj)
open EventyayOrganizer.xcworkspace
```

Always open the `.xcworkspace`, not `.xcodeproj`, after running `pod install`.

## Build & Run

Use Xcode — select a simulator or connected device and press Run (⌘R).

```bash
# From the command line (requires Xcode tools)
xcodebuild -workspace EventyayOrganizer.xcworkspace \
           -scheme EventyayOrganizer \
           -destination 'platform=iOS Simulator,name=iPhone 15' \
           build
```

## Key Dependencies

| Pod | Purpose |
|---|---|
| `Alamofire ~> 4.7` | HTTP networking |
| `SwiftLint` | Code style linting |
| `Material` | UI components |
| `M13Checkbox` | Checkbox UI component |

## API Configuration

The server base URL is set in the app's network layer. To point it at your local Open Event server, update the base URL constant to your machine's LAN IP (e.g. `http://192.168.x.x:8080/v1`). Do not use `localhost` — the iOS simulator cannot reach the host machine via `localhost` on some setups; use the LAN IP from the root `.env` → `SERVER_HOST`.

## Architecture

- **Networking:** Alamofire with a JSON:API response handler
- **Auth:** JWT token stored in Keychain; passed as `Authorization: JWT <token>` header
- **Check-in flow:** Scan QR/barcode → verify attendee via Open Event API → record check-in → middleware pushes to KHSC

## Lint

SwiftLint runs automatically as a build phase. Fix warnings before committing:
```bash
swiftlint lint --path EventyayOrganizer/
swiftlint autocorrect --path EventyayOrganizer/
```
