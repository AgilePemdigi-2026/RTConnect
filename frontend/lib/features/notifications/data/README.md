# Notifications Data

## Overview
Provides network communication for retrieving and updating user system notifications and administrative alerts in RTConnect.

## Interface
- `NotificationRepository`:
  - `getNotifications()`: Fetches unread count and list of notification items from `/api/v1/notifications`.
  - `markAsRead(int notificationId, {bool isDibaca = true})`: Marks an individual notification as read.
  - `markAllAsRead()`: Marks all unread notifications for the authenticated user as read.

## Invariants
- Default parameter for `markAsRead` sets `is_dibaca` to `true`.
- Falls back to an empty notification map if the backend data envelope contains null.

## Side Effects
- Makes HTTP GET and PUT requests to `/api/v1/notifications`, `/api/v1/notifications/<id>/read`, and `/api/v1/notifications/read-all`.

## Verification
- Run: `cd frontend && flutter test`
