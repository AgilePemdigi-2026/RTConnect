# Constants

## Overview
Provides application-wide constants, compile-time and runtime environment configuration, dynamic API base URL resolution, and centralized keys for secure storage across the RTConnect Flutter application.

## Interface
- `AppConstants`: Main constants container class.
  - `AppConstants.appName`: Static string containing `'RTConnect'`.
  - `AppConstants.rtArea`: Target RT/RW coverage area resolved from compile-time environment (`RT_AREA`, default `'RT 04 / RW 09 Gunungsari Indah'`).
  - `AppConstants.appTagline`: Dynamic tagline formatted as `'Aplikasi Administrasi Warga $rtArea'`.
  - `AppConstants.customBaseUrl`: Static mutable string allowing in-app runtime override of the API base URL.
  - `AppConstants.defaultBaseUrl`: Dynamic getter resolving the effective API base URL across web, Android emulator (`10.0.2.2:5000`), local host (`127.0.0.1:5000/api/v1`), custom runtime setting, and `--dart-define=API_BASE_URL`.
  - `AppConstants.keyAuthToken`: Storage key string `'auth_token'` for JWT session tokens.
  - `AppConstants.keyUserRole`: Storage key string `'user_role'` for user authorization role.
  - `AppConstants.keyUserId`: Storage key string `'user_id'` for logged-in user identifier.
  - `AppConstants.keyUserNik`: Storage key string `'user_nik'` for resident NIK.
  - `AppConstants.keyUserName`: Storage key string `'user_name'` for resident display name.
  - `AppConstants.keyCustomBaseUrl`: Storage key string `'custom_base_url'` for custom server URL preference.

## Invariants
- `defaultBaseUrl` always strips trailing slashes (`replaceFirst(RegExp(r'/+$'), '')`).
- All API base URLs must include the API version path segment (`/api/v1`).
- Custom base URL (`customBaseUrl`) takes precedence over build-time and platform defaults when present and non-empty.
- In production/release builds, the API base URL must use HTTPS (enforced at the network client level).

## Side Effects
- Reads compile-time environment variables via `String.fromEnvironment`.
- Inspects runtime browser URL origin and host via `Uri.base` when running on web (`kIsWeb`).

## Verification
- Run: `cd frontend && flutter test`
