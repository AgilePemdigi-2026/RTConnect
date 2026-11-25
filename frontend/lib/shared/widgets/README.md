# Shared Widgets

## Overview
Reusable UI primitives and navigation components for RTConnect's Flutter client application. Implements design system specifications grounded in Figma Hi-Fi tokens (`AppColors`, `AppSpacing`, `AppTypography`) for navigation, form inputs, status displays, and actions across resident (`warga`) and RT administrator interfaces.

## Interface
- `RTAppBar`: Standard application bar implementing `PreferredSizeWidget` with leading drawer trigger, optional branding badge ('logo' + title), and custom action slots (`rt_app_bar.dart`).
- `RTBottomNavBar`: Translucent blurred persistent bottom navigation bar rendering fixed tabs for 'Pengajuan' (index 0), 'Beranda' (index 1), and 'TanyaRT' (index 2) (`rt_bottom_nav_bar.dart`).
- `RTDrawerMenu`: Riverpod-integrated side drawer (`ConsumerWidget`) displaying user profile avatar, role badge (`Ketua RT` vs `Warga`), dynamic routing menu items, unread notification counter, and account logout action (`rt_drawer_menu.dart`).
- `RTPrimaryButton`: Full-width styled primary action button with elevation shadow, optional prefix/trailing icons, and integrated `CircularProgressIndicator` during loading state (`rt_primary_button.dart`).
- `RTSecondaryButton`: Full-width outlined secondary action button with subtle border, soft drop shadow, and optional icon (`rt_secondary_button.dart`).
- `RTStatusBadge`: Pill badge (9999px border radius) mapping document request lifecycle status strings case-insensitively to corresponding design tokens and localized labels, with optional leading indicator dot (`rt_status_badge.dart`).
- `RTTextField`: Labeled form input field (`StatefulWidget`) supporting validation, obscure text toggle for passwords, character counter, helper notes, and custom prefix/suffix icons (`rt_text_field.dart`).

## Invariants
- `RTAppBar` preferred height is strictly `kToolbarHeight + 1.0` to accommodate a 1px bottom border divider.
- `RTBottomNavBar` index contract strictly requires 3 navigation items: index 0 (Pengajuan), index 1 (Beranda), index 2 (TanyaRT).
- `RTDrawerMenu` derives user authentication details and role directly from `authControllerProvider` unless explicitly overridden via widget parameters; displays 'Ketua RT' badge and navigates to `RouteNames.rtQueue` if role is 'rt', otherwise displays 'Warga' badge and navigates to `RouteNames.wargaPengajuan`.
- `RTPrimaryButton` disables interaction (`onPressed: null`) and replaces content with a spinner whenever `isLoading` is true.
- `RTSecondaryButton` adheres to 48px standard touch height and 12px border radius by default.
- `RTStatusBadge` strictly standardizes status strings (`diajukan`, `menunggu_review`, `diproses`, `perlu_revisi`, `menunggu`, `disetujui`, `siap_diambil`, `selesai`, `ditolak`) to standardized Indonesian badge labels and color mappings.
- `RTTextField` forces `maxLines = 1` when `isPassword` is true, automatically appends a red asterisk to the label when `isRequired` is true, and maintains obscure text state internally.

## Side Effects
- `RTDrawerMenu` navigates application routes via `GoRouter` (`context.push` / `context.go`), invalidates `notificationsProvider` on opening notifications, and triggers auth state reset via `authControllerProvider.notifier.logout()` on logout tap.
- `RTAppBar` triggers `Scaffold.of(context).openDrawer()` when the menu icon button is tapped without a custom `onMenuPressed` callback.
- `RTBottomNavBar` emits index updates via `onTap(int)`.
- `RTPrimaryButton` and `RTSecondaryButton` execute provided `onPressed` callbacks upon user tap.
- `RTTextField` mutates internal password visibility state (`_obscureText`) upon toggling the visibility icon, calls `onChanged(String)`, and updates the attached `TextEditingController`.

## Verification
- Run: `cd frontend && flutter test`
