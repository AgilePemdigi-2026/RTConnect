# Auth Domain

## Overview
Defines core business domain models and client-side validation rules for user authentication and identity verification within RTConnect.

## Interface
- `UserEntity`: Immutable domain entity representing an authenticated user, supporting serialization (`fromJson`, `toJson`) and role-based status helpers (`isRT`, `isWarga`).
- `AuthValidators`: Static utility methods for form input validation:
  - `validateNIK(String? value)` / `validateNik(String? value)`: Validates 16-digit numeric national identification number.
  - `validatePhone(String? value)`: Validates 10 to 15 digit telephone numbers.
  - `validateEmail(String? value)`: Validates email address format via regex.
  - `validatePassword(String? value)`: Validates minimum 6-character length for existing passwords.
  - `validateNewPassword(String? value)`: Enforces password policy (minimum 12 characters, maximum 72 UTF-8 bytes).
  - `validateRequired(String? value, String fieldName)`: Validates non-empty required fields.

## Invariants
- `UserEntity` role comparison is case-insensitive for `isRT` (`'rt'`) and `isWarga` (`'warga'`).
- NIK must strictly contain exactly 16 numeric digits without whitespace or letters.
- New passwords must not exceed 72 bytes (Bcrypt input length constraint).

## Side Effects
- Pure business logic and domain model mapping; no external side effects or I/O operations.

## Verification
- Run: `cd frontend && flutter test`
