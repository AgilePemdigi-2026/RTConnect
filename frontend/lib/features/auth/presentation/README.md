# Auth Presentation

## Overview
Houses the user interface screens, form handling, and Riverpod state controllers for onboarding, login, registration, and session lifecycle management.

## Interface
- `AuthState`: Immutable state class containing `isLoading`, `user`, `errorMessage`, and `isAuthenticated`.
- `authRepositoryProvider`: Riverpod `Provider<AuthRepository>` dependency injection provider.
- `authControllerProvider`: Riverpod `StateNotifierProvider<AuthController, AuthState>`.
- `AuthController`: Manages authentication workflow:
  - `checkAuthStatus()`: Checks persistent storage for active tokens and hydrates profile.
  - `login(String identity, String password)`: Executes user login.
  - `register(...)`: Executes user registration with optional digital signature upload.
  - `logout()`: Clears authentication state and storage.
  - `updateCurrentUser(UserEntity user)`: Updates local user entity in memory.
- `LandingScreen`: Welcome and onboarding view with routing to login and registration.
- `LoginScreen`: Form for user credentials with configurable API server host configuration.
- `RegisterScreen`: Multi-field registration form including identity data and signature file picker.

## Invariants
- `AuthController` triggers `checkAuthStatus()` immediately upon construction.
- Logout resets `AuthState` to default unauthenticated state (`AuthState()`).
- Error messages from exceptions are stripped of the `'Exception: '` prefix before presentation.

## Side Effects
- Mutates Riverpod state across the application.
- Updates navigation stack via `go_router`.
- Reads and updates custom base URL setting in `FlutterSecureStorage`.
- Selects files from device storage using `file_picker`.

## Verification
- Run: `cd frontend && flutter test`
