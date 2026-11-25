# Pengajuan RT Demo

## Overview
Standalone demonstration module for RT officials to manage citizen letter submissions (kelola & detail pengajuan). Note that this is a legacy standalone demo module running against `/api/rt/pengajuan` (or offline via `MockPengajuanRtService` in `lib/main_demo_rt.dart`); the live production UI resides in `lib/features/letters/` communicating with `/api/v1/letters`.

## Interface
- `RtColors`: Color palette constants conforming to Figma designs (`primary`, `navy`, `success`, `danger`, `warning`, `bg`, `card`, `muted`, `field`).
- `StatusStyle`: Visual styling attributes (foreground, background, accent border color) mapped to each `StatusPengajuan`.
- `StatusChip`: Reusable status pill widget rendered according to `StatusPengajuan`.
- `formatTanggalSingkat(DateTime d)`: Formats date to Indonesian short timestamp (e.g., `17 Agu 2026 • 09.42 WIB`).
- `formatTanggalPanjang(DateTime d)`: Formats date to Indonesian extended timestamp (e.g., `17 Agustus 2026 / 09.42 WIB`).
- Subdirectories:
  - `models`: [./models/README.md](./models/README.md) - Submission data models and status enumerations.
  - `pages`: [./pages/README.md](./pages/README.md) - RT management and detail submission view screens.
  - `services`: [./services/README.md](./services/README.md) - Service abstraction, API client, and offline mock implementation.
  - `widgets`: [./widgets/README.md](./widgets/README.md) - Modal dialogs for notes and PIN authorization.

## Invariants
- Direct source file `rt_theme.dart` provides shared styling tokens for all pages and widgets in this module.
- Requires Flutter 3.24+ due to reliance on `PopScope.onPopInvokedWithResult`.
- Offline mock security PIN is `482913` (locks out for 15 minutes after 5 consecutive failed attempts).

## Side Effects
- When wired to `ApiPengajuanRtService`, dispatches HTTP requests to `/rt/pengajuan/*`.
- When using `MockPengajuanRtService`, mutates local in-memory submission lists.

## Developer & Demo Execution Context
### Running Standalone Demo
1. Ensure `http: ^1.2.0` dependency is present in `pubspec.yaml`.
2. Run `flutter pub get`.
3. Launch via `flutter run -t lib/main_demo_rt.dart`.
4. Mock PIN: **482913** (locked for 15 minutes after 5 failed tries).

### Connecting to Backend
In `lib/main_demo_rt.dart`, swap `MockPengajuanRtService()` with:
```dart
ApiPengajuanRtService(
  baseUrl: 'http://10.0.2.2:5000/api', // Android emulator to host
  tokenProvider: () => tokenJwtYangTersimpan,
)
```

Used Endpoints:
| Action | Method & Path | Body |
|---|---|---|
| List Submissions | `GET /rt/pengajuan` | |
| Submission Detail | `GET /rt/pengajuan/<id>` | |
| Request Revision | `POST /rt/pengajuan/<id>/revisi` | `catatan_revisi` |
| Reject | `POST /rt/pengajuan/<id>/tolak` | `alasan_penolakan` |
| Approve (Physical) | `POST /rt/pengajuan/<id>/setuju` | |
| Ratify (Digital) | `POST /rt/pengajuan/<id>/sahkan-digital` | `pin` |

Response envelope: `{"status": "success"|"error", "message": "...", "nomor_surat"?, "sisa_percobaan"?, "sisa_menit"?}`

## Verification
- Run: `cd frontend && flutter test`
