# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Event Frontend is an **Ember.js** application (v4.x) that serves as the front end for the Open Event Server. It uses **ember-data** with the **JSON:API** spec to communicate with the backend REST API.

## Setup

```sh
yarn
cp .env.example .env
yarn l10n:generate
```

The `.env` file controls `API_HOST` (defaults to `https://test-api.eventyay.com` for development), `FASTBOOT_DISABLED`, and optional tokens for Mapbox and hCaptcha.

## Common Commands

```sh
yarn start               # Dev server at http://localhost:4200
yarn build               # Development build
yarn build -prod         # Production build
yarn test                # Run tests headlessly in Chrome
yarn test --server       # Run tests with live browser
yarn exam                # Run tests in random order (uses ember-exam)
yarn lint                # Run all linters (JS, SCSS, HBS)
yarn lint:js             # ESLint with autofix
yarn lint:hbs            # ember-template-lint with autofix
yarn l10n:extract        # Extract new translation strings
yarn l10n:generate       # Generate translation files (required after clone)
```

To run a single test file, use the `--filter` flag or target a specific module:
```sh
ember test --filter "acceptance/events"
```

Note: linting runs automatically as a pre-commit hook.

## Architecture

### Framework & Data Layer

- **Ember.js** with classic + Octane (Glimmer) components mixed — older code uses `Mixin`/`extend()`, newer code uses native classes with decorators (`@service`, `@tracked`, `@action`).
- **ember-data** with **JSON:API** adapter (`app/adapters/application.js`). The adapter automatically attaches JWT auth headers and handles 401 → session invalidation.
- The serializer (`app/serializers/application.js`) extends `JSONAPISerializer` with `EventRelationMixin` which swaps event identifiers (slug ↔ numeric ID) on serialization.
- Filters sent to the API must be JSON-stringified — `fixFilterQuery` in the adapter handles this.
- Authentication is via JWT tokens using `ember-simple-auth` + `ember-simple-auth-token`. The `session` service tracks auth state.

### Key Directories

| Path | Purpose |
|------|---------|
| `app/models/` | ember-data models (JSON:API resources) |
| `app/routes/` | Route classes — handle model hooks and redirects |
| `app/controllers/` | Controller classes — handle actions and UI state |
| `app/components/` | Reusable UI components (mix of classic and Glimmer) |
| `app/templates/` | Handlebars templates |
| `app/services/` | Injectable services (auth, l10n, notifications, settings, etc.) |
| `app/mixins/` | Shared behavior (form validation, event-relation serialization, ember-table) |
| `app/adapters/` | ember-data network layer |
| `app/serializers/` | JSON:API serialization/deserialization |
| `app/utils/` | Pure utility functions |
| `app/helpers/` | Handlebars template helpers |
| `translations/` | i18n string files (JSON); managed via `ember-l10n` |

### Route Structure

Major route namespaces:
- `/e/:event_id/` — public event pages (sessions, speakers, CFS)
- `/events/` — organizer event management
- `/admin/` — admin panel
- `/account/` — user account settings
- `/orders/` — ticket orders
- `/groups/` — event groups

### Form Handling

Forms use `mixins/form.js` which wraps Fomantic UI's form validation. Components using forms should extend this mixin. Validation rules are defined per-component in `getValidationRules()`.

### Internationalisation

Strings are wrapped with `this.l10n.t('...')` in JS or `{{t '...'}}` in templates. After adding new strings, run `yarn l10n:extract` then `yarn l10n:generate`.

### Attribute Options

Model attributes accept `readOnly: true` option — the serializer (`serializeAttribute`) skips these when sending data to the server unless explicitly overridden with `includeReadOnly`.

## Tests

Tests live in `tests/` with three categories:
- `tests/acceptance/` — full app integration tests
- `tests/integration/` — component/helper tests
- `tests/unit/` — model/service/util unit tests

Test helper setup is in `tests/test-helper.js`. The test runner is `testem` using headless Chrome.
