# Profile Presentation

## Overview
Provides screens and state controllers for viewing user profile data, editing personal contact info, capturing and updating digital signatures, and managing profile avatars.

## Interface
- `ProfileState`: Immutable state containing loading indicators (`isLoading`, `isSignatureLoading`, `isAvatarLoading`), error and success notifications, signature bytes and timestamp, and avatar bytes.
- `profileRepositoryProvider`: Riverpod provider exposing `ProfileRepository`.
- `profileControllerProvider`: Riverpod `StateNotifierProvider<ProfileController, ProfileState>`.
- `ProfileController`:
  - `loadSignature([String? customPath])`: Asynchronously fetches digital signature bytes.
  - `loadAvatar([String? customPath])`: Asynchronously fetches avatar picture bytes.
  - `updateProfile(...)`: Submits profile changes and synchronizes the active `UserEntity` in `AuthController`.
  - `updateSignature(...)`: Submits signature file bytes or path, updates active user entity, and stores byte cache.
  - `updateAvatar(...)`: Submits avatar file bytes, updates active user entity, and stores byte cache.
  - `refreshProfile()`: Reloads user profile data from backend.
- `ProfileScreen`: Primary account view displaying profile metadata, avatar, digital signature preview, and settings actions.
- `EditProfileScreen`: Form interface to modify name, phone number, address, and email.
- `SignatureScreen`: Canvas signature drawing and image upload interface.

## Invariants
- Updating profile, signature, or avatar automatically updates the current user model in `authControllerProvider` to maintain app-wide consistency.
- Error strings strip the `'Exception: '` prefix prior to state assignment.

## Side Effects
- Updates Riverpod state for both profile and authentication modules.
- Triggers image picking and canvas byte conversion on device.

## Verification
- Run: `cd frontend && flutter test`
