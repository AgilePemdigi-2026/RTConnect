# Errors

## Overview
Defines standard domain exceptions and error models for RTConnect. These classes translate low-level network and server failures into user-friendly, localized error representations with consistent error codes.

## Interface
- `AppException`: Base exception class implementing `Exception`.
  - Field: `final String message`
  - Field: `final String? code`
  - Method: `String toString()` returns `message`.
- `NetworkException`: Specialization for network connectivity issues.
  - Default message: `'Koneksi jaringan terputus. Silakan coba lagi.'`
  - Code: `'NETWORK_ERROR'`
- `AuthException`: Specialization for credential, session, and authentication errors.
  - Default message: `'Email/NIK atau password salah.'`
  - Code: `'AUTH_ERROR'`
- `ValidationException`: Specialization for client or server validation rejections.
  - Code: `'VALIDATION_ERROR'`
- `ServerException`: Specialization for HTTP 5xx or unhandled server-side exceptions.
  - Default message: `'Terjadi kesalahan pada server.'`
  - Code: `'SERVER_ERROR'`

## Invariants
- All domain exceptions must inherit from `AppException`.
- `toString()` always delegates directly to `message` to prevent technical exception class prefixes from leaking into the UI.
- Subclasses maintain distinct, machine-readable uppercase error codes (`NETWORK_ERROR`, `AUTH_ERROR`, `VALIDATION_ERROR`, `SERVER_ERROR`).

## Side Effects
- None. These exception models are pure and immutable.

## Verification
- Run: `cd frontend && flutter test`
