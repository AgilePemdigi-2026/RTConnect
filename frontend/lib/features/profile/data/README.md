# Profile Data

## Overview
Provides network communication and byte stream retrieval for user profiles, profile editing, digital signature uploads, and avatar image management.

## Interface
- `ProfileRepository`:
  - `getProfile()`: Retrieves user profile entity from `/api/v1/auth/me`.
  - `updateProfile(...)`: Sends updated personal details (name, phone, address, email) via PUT to `/api/v1/users/profile`.
  - `updateSignature(...)`: Uploads new digital signature as file bytes, file path multipart, or preset signature key to `/api/v1/users/signature`.
  - `getSignatureBytes([String? customPath])`: Fetches raw image bytes of digital signature.
  - `updateAvatar(...)`: Uploads profile avatar photo as multipart payload to `/api/v1/users/avatar`.
  - `getAvatarBytes([String? customPath])`: Fetches raw image bytes of user avatar.

## Invariants
- `updateSignature` throws an `ArgumentError` if no valid byte array, file path, or signature key is provided.
- Byte fetch methods return `null` upon network failures or empty responses without throwing unhandled exceptions.

## Side Effects
- Makes HTTP GET, PUT, and POST requests against `/api/v1/users/*` and `/api/v1/auth/me`.
- Encodes image bytes as `MultipartFile` for upload payloads.

## Verification
- Run: `cd frontend && flutter test`
