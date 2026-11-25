# Notifications Presentation

## Overview
Presents the notification feed screen and manages Riverpod reactive providers for notification streams and unread badge counters.

## Interface
- `notificationRepositoryProvider`: Riverpod provider exposing `NotificationRepository`.
- `notificationsProvider`: FutureProvider loading notification items and unread count; returns empty list if user is unauthenticated.
- `unreadNotificationCountProvider`: Provider deriving integer count of unread notifications from `notificationsProvider`.
- `NotificationFeedScreen`: Screen rendering list of notification cards with empty states, deep linking, and bulk "mark all as read" app bar action.

## Invariants
- `notificationsProvider` guards against unauthenticated calls by checking `authState.isAuthenticated` before making network requests.
- `unreadNotificationCountProvider` defaults safely to `0` when loading or in error state.

## Side Effects
- Invokes remote API mutation (`markAllAsRead`) and invalidates `notificationsProvider` for state refresh.
- Updates UI navigation upon tapping notification items.

## Verification
- Run: `cd frontend && flutter test`
