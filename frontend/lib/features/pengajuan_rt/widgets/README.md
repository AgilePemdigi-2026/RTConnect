# Pengajuan RT Widgets

## Overview
Provides reusable dialog and bottom sheet UI components for capturing notes and PIN authorization in the RT submission demo module.

## Interface
- `showCatatanSheet(...)`: Displays a modal bottom sheet allowing the RT official to input mandatory notes for revision requests or rejection reasons.
- `showPinKeamananDialog(...)`: Displays an uncancelable modal dialog for 6-digit PIN entry to authorize digital ratification.

## Invariants
- `showCatatanSheet` strictly requires non-empty text input before allowing confirmation.
- `showPinKeamananDialog` validates that the PIN is exactly 6 digits before invoking the `onSubmit` callback.
- `showPinKeamananDialog` disables touch-outside dismissal (`barrierDismissible: false`).

## Side Effects
- Opens and closes modal overlays in the Flutter navigation tree.
- Triggers asynchronous submission callbacks.

## Verification
- Run: `cd frontend && flutter test`
