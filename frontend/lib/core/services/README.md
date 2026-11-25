# Services

## Overview
Provides core background and infrastructure services for RTConnect, specifically push notification lifecycle management using Firebase Cloud Messaging (FCM) and Flutter Local Notifications.

## Interface
- `PushNotificationService`: Static platform service for notification orchestration.
  - Method: `static Future<void> initialize()`: Initializes Firebase Core, background handlers, Android notification channels, local notification plugins, and sets up foreground, background, and terminated tap handlers.
  - Method: `static Future<bool> requestPermission()`: Prompts the user for push notification permissions across Android and iOS.
  - Method: `static Future<void> syncDeviceToken(ApiClient apiClient)`: Requests permission, retrieves the active FCM token, listens for token refreshes, and registers the token with the backend API (`/auth/device-token`).
  - Method: `static Future<void> removeDeviceToken(ApiClient apiClient)`: Cancels token subscriptions and deregisters the FCM token from the backend upon user logout.
- `_firebaseMessagingBackgroundHandler(RemoteMessage message)`: Top-level background message callback marked with `@pragma('vm:entry-point')`.

## Invariants
- `initialize()` is guarded by `_isInitialized` and will execute its setup logic at most once per app lifecycle.
- The background message handler must remain a top-level function annotated with `@pragma('vm:entry-point')` to prevent tree-shaking and enable execution in an isolated background Dart VM.
- Notification clicks route conditionally: directly to `/letters/:id` if `pengajuan_id` is supplied, to a custom route if `tautan` is supplied, or fallback to `RouteNames.notifications`.
- Device token synchronization only proceeds when notification permissions are granted.

## Side Effects
- Registers system notification channels and displays heads-up banners on Android via `FlutterLocalNotificationsPlugin`.
- Subscribes to Firebase Cloud Messaging streams (`onMessage`, `onMessageOpenedApp`, `onTokenRefresh`).
- Dispatches HTTP POST and DELETE requests to `/auth/device-token` via `ApiClient`.
- Triggers deep-link navigation in `appRouter`.

## Verification
- Run: `cd frontend && flutter test`
