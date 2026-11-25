# Auth Data

## Overview
Provides data layer access and credential persistence for authentication and authorization in the RTConnect application. It manages HTTP network operations with the backend API and persists session state in secure device storage.

## Interface
- `AuthRepository`: Handles user login, registration, current user profile fetching, role retrieval, session validation, logout, and push notification device token synchronization.
  - `login(String identity, String password)`: Authenticates user and caches credentials.
  - `register(...)`: Registers a new resident account with optional signature upload.
  - `getCurrentUser()`: Fetches the authenticated user profile; clears cached credentials on 401/AuthException.
  - `getSavedRole()`: Reads cached role from secure storage.
  - `isAuthenticated()`: Checks if an authentication token exists.
  - `logout()`: Deregisters push notification token and clears all secure storage authentication keys.
  - `syncDeviceToken()`: Synchronizes device token for FCM notifications.

## Invariants
- Successful login must store auth token, role, user ID, user name, and NIK into `FlutterSecureStorage`.
- When token validation fails (HTTP 401 or `AuthException`), authentication credentials must be wiped while preserving non-auth configuration (such as custom server URL).
- Registration with a signature must format the request as `multipart/form-data` with `signature_<nik>.png`.

## Side Effects
- Makes HTTP POST and GET requests to `/api/v1/auth/login`, `/api/v1/auth/register`, and `/api/v1/auth/me`.
- Reads, writes, and deletes secure hardware/keystore storage entries via `FlutterSecureStorage`.
- Dispatches FCM device tokens through `PushNotificationService`.

## Verification
- Run: `cd frontend && flutter test`
