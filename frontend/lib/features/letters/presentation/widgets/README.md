# Letters Presentation Widgets

## Overview
Reusable specialized widgets for letter preview formatting and administrative PIN authorization dialogs within the letter management feature.

## Interface
- `SuratIdentitas`: Constants containing official RT metadata (RT number, RW number, kelurahan, city, official names).
- `BlangkoPreview`: Widget rendering an on-screen preview replicating the exact formal layout of Indonesian RT introductory/certificate letters (surat pengantar / keterangan RT), styled to match backend PDF output.
- `PinAuthDialog`: Modal dialog prompting the RT leader for a 6-digit security PIN to authorize digital document signing, with validation and async submission handling.
  - `PinAuthDialog.show(...)`: Static helper to launch the dialog modal.

## Invariants
- `SuratIdentitas` constants must align with backend environment configurations (`RT_NUMBER`, `RW_NUMBER`, `RT_KELURAHAN`).
- `PinAuthDialog` strictly requires exactly 6 numeric characters before permitting submission.
- `PinAuthDialog` blocks modal dismissal during execution (`barrierDismissible: false`).

## Side Effects
- Invokes provided asynchronous confirmation callbacks (`onConfirm`).
- Reads user input and shows error feedback.

## Verification
- Run: `cd frontend && flutter test`
