# Network

## Overview
Provides the centralized HTTP client configuration and REST API endpoints mapping for the RTConnect client. Manages Dio instances, base URL selection, bearer token injection via secure storage, release HTTPS validation, automatic session expiration handling, and exception normalization.

## Interface
- `ApiEndpoints`: Static container for REST API route paths.
  - Auth & Profile: `register` (`/auth/register`), `login` (`/auth/login`), `me` (`/auth/me`), `updateProfile` (`/auth/me`), `updateSignature` (`/auth/signature`), `getSignature` (`/auth/signature`), `updateAvatar` (`/auth/avatar`), `getAvatar` (`/auth/avatar`), `deviceToken` (`/auth/device-token`), `fileUrl(String path)`.
  - Letters: `letterTypes` (`/letters/types`), `applyLetter` (`/letters/apply`), `myApplications` (`/letters/my-applications`), `myLastApplicantData` (`/letters/my-last-data`), `aiFill` (`/letters/ai-fill`), `incomingQueue` (`/letters/incoming-queue`), `letterDetail(int id)`, `resubmitLetter(int id)`, `letterDecision(int id)`, `signDigital(int id)`, `confirmPhysical(int id)`, `downloadLetter(int id)`, `downloadLetterLink(int id)`.
  - Chatbot & Notifications: `chatbotQuery` (`/chatbot/query`), `notifications` (`/notifications`).
- `ApiClient`: Centralized HTTP client wrapper around Dio.
  - Constructor: `ApiClient({String? baseUrl})` initializes Dio with standard timeouts and headers.
  - Property: `Dio get dio => _dio`.
  - Interceptors:
    - `onRequest`: Resolves dynamic baseUrl from `FlutterSecureStorage` (`keyCustomBaseUrl`) or defaults, validates URL scheme and authority, enforces HTTPS in `kReleaseMode`, and injects `Authorization: Bearer <token>` from `keyAuthToken`.
    - `onError`: Handles HTTP 401 unauthenticated responses by purging stored credentials, avoiding purges on `/auth/login` or RT PIN errors (`INVALID_PIN` / `PIN_LOCKED`), and maps Dio errors into typed `AppException` instances (`NetworkException`, `AuthException`, `ValidationException`, `ServerException`).

## Invariants
- All outgoing HTTP requests automatically append `bypass-tunnel-reminder: true` and JSON content headers.
- In `kReleaseMode`, non-HTTPS API URLs are immediately rejected with a `DioException` wrapping `FormatException`.
- Base URLs always have trailing slashes stripped.
- Authentication tokens are read from secure storage per request and injected as `Authorization: Bearer <token>`.
- Receiving a 401 Unauthorized on authenticated requests clears all stored credentials (`auth_token`, `user_role`, `user_id`, `user_name`, `user_nik`), except when the failure is a login attempt or RT digital signature PIN error.

## Side Effects
- Performs outbound network I/O over HTTP/HTTPS.
- Asynchronously reads and clears credentials in device secure storage (`FlutterSecureStorage`).

## Verification
- Run: `cd frontend && flutter test`
