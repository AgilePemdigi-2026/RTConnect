# Authentication & Authorization Middleware

## Overview
Request interception and access control middleware for the RTConnect Flask REST API. Provides JWT generation, Bearer token verification, user activity validation against the database, and Role-Based Access Control (RBAC) decorators enforcing endpoint authorization boundaries.

## Interface
- `generate_token(user_id: int, role: str, email: str) -> str`: Issues signed HS256 JWT containing subject ID, role, email, issuance timestamp (`iat`), and expiration timestamp (`exp`).
- `jwt_required(f)`: Route decorator verifying incoming JWTs via `Authorization: Bearer <token>` header or `token` query param. Validates token signature, fetches the user via `get_user()`, checks that the user exists and is active, and attaches the user dictionary to `request.current_user`. Returns 401 JSON envelope on missing or expired tokens.
- `roles_accepted(*allowed_roles)`: Route decorator enforcing RBAC. Asserts `request.current_user['role']` matches one of the permitted roles (`'warga'`, `'rt'`, `'admin'`), returning 403 `FORBIDDEN` if unauthorized.

## Invariants
- Execution order: Protected routes requiring role authorization must declare `@jwt_required` before `@roles_accepted(...)`.
- Cryptographic consistency: Tokens are encoded and validated strictly using `Config.JWT_SECRET` with the `HS256` algorithm.
- Active status validation: A syntactically and cryptographically valid token is rejected with 401 `UNAUTHORIZED` if the underlying database record is deactivated (`is_active = false`) or deleted.
- Standard error envelope: All authentication and authorization failures return HTTP 401 or 403 with the canonical envelope `{success: False, message: str, data: None, error: str}`.

## Side Effects
- Mutates the Flask request context by setting `request.current_user` and request start timer `request._t_req_start`.
- Performs a database query via `get_user()` to verify user existence and active status on each authenticated request.

## Verification
- Run: `cd backend && python test_api.py`
