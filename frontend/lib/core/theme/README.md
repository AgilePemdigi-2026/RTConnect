# Theme

## Overview
Encapsulates design tokens, typography, spacing, and Material 3 theme configuration for RTConnect, grounded in the Figma Hi-Fi design system specification.

## Interface
- `AppColors`: Palette of brand, surface, text, and semantic status colors.
  - Brand Blues: `primaryBrand` (`#1D4ED8`), `primaryAction` (`#2563EB`), `primaryDark` (`#1E40AF`), `primaryLight` (`#3B82F6`), `primaryAccent` (`#0051D5`), `primaryContainer` (`#DBEAFE`), `primaryBg` (`#EFF6FF`), `lightContainer` (`#EDF0FF`).
  - Navy Tones: `navyDark` (`#00152A`), `navyDeep` (`#0B1C30`), `navyHeader` (`#102A43`), `secondaryDark` (`#0F172A`).
  - Status & Badges: `statusDiajukan`, `statusRevisi`, `statusMenunggu`, `statusDisetujui`, `statusSelesai`, `statusDitolak`, `statusSiapDiambil` (each with matching foreground and background container colors).
  - Utilities & Chat: `brandWhatsApp` (`#059669`), `success`, `error`, `warning`, `badgeNotification`, `chatBubbleBot`, `chatBubbleUser`.
- `AppSpacing`: Spatial tokens, radii, and component layout metrics based on an 8dp grid.
  - Spacing steps: `space2XS` (4dp), `spaceXS` / `xs` (8dp), `spaceSM` / `sm` (12dp), `spaceMD` / `md` (16dp), `spaceLG` / `lg` (24dp), `spaceXL` / `xl` (32dp), `space2XL` (48dp).
  - Radii: `radiusXS` (4dp), `radiusSM` (8dp), `radiusMD` (12dp), `radiusLG` (16dp), `radiusFull` (999dp).
  - Metrics: `minTouchTarget` (48dp), `buttonHeight` (48dp), `inputHeight` (48dp), `bottomNavHeight` (64dp), `avatarDiameter` (56dp).
- `AppTypography`: Typography definitions using Google Fonts Plus Jakarta Sans.
  - Hierarchy: `heroTitle` (30sp/w800), `displayLarge` (28sp/w700), `titleLarge` / `heading1` (24sp/w700), `titleMedium` / `heading2` (18sp/w700), `titleSmall` / `heading3` (16sp/w600), `bodyLarge` (14sp/w500), `bodyMedium` (13sp/w400), `bodySmall` (12sp/w400), `labelLarge` (14sp/w700), `labelMedium` / `labelBold` (12sp/w700), `labelSmall` (11sp/w600), `caption` (11sp/w500), `badgeUppercase` (11sp/w700), `buttonLabel` (14sp/w700).
- `AppTheme`: Global theme builder.
  - Property: `static ThemeData get lightTheme`: Constructs Material 3 `ThemeData` wiring `AppColors`, `AppSpacing`, and `AppTypography` into `ColorScheme`, `AppBarTheme`, `CardThemeData`, and `InputDecorationTheme`.

## Invariants
- Application must run with Material 3 enabled (`useMaterial3: true`).
- All interactive controls (buttons, inputs) must maintain a minimum touch target height of at least 48dp (`AppSpacing.minTouchTarget`).
- Font family is strictly standardized to Plus Jakarta Sans.
- Cards default to zero elevation with a 1dp border (`AppColors.border`) and 16dp border radius.

## Side Effects
- Asynchronously loads and caches Google Fonts (Plus Jakarta Sans) font files at runtime.

## Verification
- Run: `cd frontend && flutter test`
