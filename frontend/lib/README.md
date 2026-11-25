# Frontend Application Library (lib)

## Overview
Root application package for RTConnect's Flutter client. Houses the application entry point (`main.dart`), root widget configuration (`RTConnectApp`), and coordinates foundational core infrastructure, modular feature domains, and shared presentation primitives.

## Interface
- `main()`: Top-level async entry point initializing Flutter engine bindings and Firebase push notifications before mounting the root `ProviderScope`.
- `RTConnectApp`: Root `StatelessWidget` configuring `MaterialApp.router` with `AppConstants.appName`, `AppTheme.lightTheme`, and `appRouter`.
- Subdirectories:
  - [Core](./core/README.md): App-wide configuration, network clients, error models, router, push services, and design tokens.
  - [Features](./features/README.md): Modular business feature packages (auth, chatbot, home, letters, notifications, pengajuan_rt demo, profile).
  - [Shared](./shared/README.md): Reusable UI primitives and navigation components.

## Invariants
- `WidgetsFlutterBinding.ensureInitialized()` and `PushNotificationService.initialize()` must complete before `runApp()`.
- Global state is encapsulated within root `ProviderScope`.
- Routing is managed exclusively via GoRouter (`appRouter`) configured in `MaterialApp.router`.
- Visual styling adheres strictly to `AppTheme.lightTheme`.

## Side Effects
- Initializes Firebase Cloud Messaging streams and background listeners.
- Mounts widget tree into platform window surface.

## Verification
- Run: `cd frontend && flutter test`
