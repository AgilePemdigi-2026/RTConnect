# BDD Feature Specifications & Test Harness

## Overview
Behavior-Driven Development (BDD) test harness coordinating Gherkin specifications and automated acceptance tests using `behave`. Contains end-to-end specifications aligned with GitHub backlog issues and development sprints, along with test execution hooks for setup, state isolation, and database teardown.

## Interface
- `environment.py`: Test runner hooks and global lifecycle management.
  - `before_all(context)`: Initializes Flask test client, mock signing PINs, and ID tracking lists for test entities.
  - `before_scenario(context, scenario)`: Resets per-scenario context attributes, request headers, and payloads.
  - `after_all(context)`: Cascades deletion of all test records created during test runs (letters, sessions, notifications, test citizens) and closes the database connection pool.
- Subdirectories & Contracts:
  - [./steps/README.md](./steps/README.md) - Gherkin step implementations mapping scenario text to Flask test client calls.
- Feature suites:
  - `sprint1/`: Core specifications covering resident authentication, basic letter requests, and TanyaRT retrieval.
  - `sprint2/`: Advanced specifications covering RT queue review, revision notes, PIN-based digital signing, and AI document assistance.

## Invariants
- Test database cleanup: Every entity created during test execution (`created_letter_ids`, `created_session_ids`, `created_user_ids`) must be explicitly deleted in `after_all` to avoid state contamination.
- Test client security: Test PINs (`123456`) and dummy WhatsApp numbers are only auto-configured when running non-production mode (`not Config.IS_PRODUCTION`).
- Traceability: Feature file tags (`@sprint1`, `@issue-9`, `@sprint2`) map directly to user stories and issue acceptance criteria.

## Side Effects
- Initializes Flask in-memory testing client.
- Performs cascading database insertions and cleanup deletions in PostgreSQL.
- Overrides runtime config attributes for testing during non-production runs.

## Verification
- Run: `cd backend && python test_api.py`
- Run all BDD features: `cd backend && python run_bdd.py`
- Run specific sprint: `cd backend && python run_bdd.py features/sprint2`
