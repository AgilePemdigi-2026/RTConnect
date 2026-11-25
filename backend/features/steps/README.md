# BDD Step Definitions

## Overview
Step definition implementations for Behavior-Driven Development (BDD) test suites using `behave`. These Python modules translate Gherkin scenario steps (`Given`, `When`, `Then`) into automated HTTP requests against the Flask test client and direct PostgreSQL assertions.

## Interface
- `auth_steps.py`: User authentication, resident self-registration, credential validation, and JWT token extraction step definitions.
  - Given steps: registration payload preparation, pre-existing resident accounts.
  - When steps: login requests, registration submission with duplicate checks.
  - Then steps: JWT token validation, database role verification (`warga`, `rt`, `admin`).
- `chatbot_steps.py`: TanyaRT conversational assistant test steps.
  - When steps: asking chatbot queries via `POST /api/v1/chatbot/query`.
  - Then steps: checking score thresholds, verification of guardrail rejections (`RAHASIA`, `LUAR_CAKUPAN`), session recording assertions.
- `common_steps.py`: Shared HTTP and response assertions.
  - Given steps: backend readiness, active user sessions.
  - When steps: authenticated and unauthenticated `GET`/`POST` requests.
  - Then steps: status code validation, JSON response envelope (`success`, `message`, `data`, `error`) checks.
- `letter_steps.py`: Administrative letter lifecycle step definitions.
  - Given steps: letter type catalog checks, existing application setups.
  - When steps: letter submission (`POST /api/v1/letters/apply`), invalid payload handling.
  - Then steps: application ID format checks, RT notification triggers.
- `sprint2_steps.py`: Advanced RT administrative workflow steps.
  - Given steps: multi-user authenticated sessions, digital signature prerequisites with PIN, mock AI responses.
  - When steps: RT review queue retrieval, approval/revision decisions, digital signature execution (`sign-digital`).
  - Then steps: official letter number assignment, audit logging, resident revision flow checks.

## Invariants
- Context isolation: State is shared across steps via `behave.runner.Context` (e.g., `context.token`, `context.client`, `context.response`); state from previous scenarios must not leak.
- Deterministic test data: Dynamic emails and usernames must use randomized or isolated identifiers to prevent unique constraint violations on repeated runs.
- JSON response conformity: All endpoints under test must return the standard RTConnect response envelope `{success, message, data, error}`.

## Side Effects
- Invokes Flask test client handlers in-memory.
- Performs database INSERT, UPDATE, and DELETE operations in the test database for fixtures and test assertions.

## Verification
- Run: `cd backend && python test_api.py`
- Run BDD: `cd backend && python run_bdd.py`
