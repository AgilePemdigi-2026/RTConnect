# Router

## Overview
Configures declarative navigation for RTConnect using GoRouter. Enforces route guards via an authentication gate, manages persistent shell navigation for primary tabs (Resident and RT Head views), and isolates sub-screens on the root navigator.

## Interface
- `RouteNames`: Static container for string route paths.
  - Public routes: `landing` (`/`), `login` (`/login`), `register` (`/register`).
  - Resident (Warga) routes: `wargaHome` (`/warga/home`), `wargaPengajuan` (`/warga/pengajuan`), `wargaPengajuanBaru` (`/warga/pengajuan/baru`), `wargaPengajuanManual` (`/warga/pengajuan/manual`), `wargaPengajuanRevisi` (`/warga/pengajuan/revisi/:id`), `chatbot` (`/chatbot`).
  - RT Head routes: `rtHome` (`/rt/home`), `rtQueue` (`/rt/pengajuan`), `rtDetail` (`/rt/pengajuan/:id`).
  - Shared Profile & Utilities: `profile` (`/profile`), `editProfile` (`/profile/edit`), `signature` (`/profile/signature`), `pdfPreview` (`/surat/preview/:id`), `notifications` (`/notifications`).
- `rootNavigatorKey`: Top-level `GlobalKey<NavigatorState>` managing full-screen sub-screens.
- `shellNavigatorKey`: Child `GlobalKey<NavigatorState>` hosting nested tab screens within `ShellRoute`.
- `appRouter`: `GoRouter` instance configuring the navigation hierarchy, redirect checks, and route endpoints.

## Invariants
- Unauthenticated users attempting to access protected routes wrapped in `_AuthGate` are redirected to `RouteNames.login`.
- Primary tabs (`wargaHome`, `wargaPengajuan`, `rtHome`, `rtQueue`, `chatbot`) are rendered within `_MainNavigationShell` containing `RTBottomNavBar`.
- Detailed sub-screens (AI Assistant, Manual Form, Revision, Letter Details, Profile, Signature, Notifications, PDF Viewer) must specify `parentNavigatorKey: rootNavigatorKey` to render above and without the bottom navigation bar.
- Tab selection index branches dynamically based on `user.isRT` role.

## Side Effects
- Mutates Flutter navigation stack and modifies browser URL/history on web.
- Watches Riverpod `authControllerProvider` to evaluate authentication states reactively.

## Verification
- Run: `cd frontend && flutter test`
