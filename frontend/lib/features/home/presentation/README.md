# Home Presentation

## Overview
Houses the primary dashboard screens for both RT administrators and citizens (Warga), aggregating application queues, quick service actions, statistics, and system notifications.

## Interface
- `RTHomeScreen`: Dashboard for RT administrators featuring incoming letter verification queue, pending request badges, verification status summary, quick actions, and navigation drawer.
- `WargaHomeScreen`: Dashboard for neighborhood residents displaying active letter submission progress, quick application shortcuts, informational banners, and notification indicators.

## Invariants
- `RTHomeScreen` watches `incomingQueueProvider` and `unreadNotificationCountProvider` to display live administrative counters.
- `WargaHomeScreen` watches `myApplicationsProvider` to present live citizen request statuses.
- Drawer and top-level navigation route dynamically based on active user role.

## Side Effects
- Reads authentication, letter queue, and notification streams via Riverpod.
- Navigates across feature screens via `go_router`.

## Verification
- Run: `cd frontend && flutter test`
