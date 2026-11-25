# Pengajuan RT Pages

## Overview
Houses standalone demo screens for RT officials to inspect, search, filter, revise, reject, and ratify citizen letter submissions.

## Interface
- `KelolaPengajuanPage`: Dashboard screen displaying the list of submissions with tab filters (`semua`, `diajukan`, `revisi`, `selesai`), search input, and sorting order toggle.
- `DetailPengajuanPage`: Detailed view of a single submission presenting citizen details, attachment downloads, dues indicators, draft letters, and action buttons for approval, revision, rejection, or digital PIN signing.

## Invariants
- `DetailPengajuanPage` pops navigation with `true` when submission status changes to trigger a refresh in `KelolaPengajuanPage`.
- Both pages require an explicit injection of `PengajuanRtService` (permitting either `ApiPengajuanRtService` or `MockPengajuanRtService`).

## Side Effects
- Invokes asynchronous network or mock methods on `PengajuanRtService`.
- Displays modal dialogs and bottom sheets (`PinKeamananDialog`, `CatatanSheet`).

## Verification
- Run: `cd frontend && flutter test`
