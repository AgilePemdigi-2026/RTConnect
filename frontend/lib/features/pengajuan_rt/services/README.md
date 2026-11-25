# Pengajuan RT Services

## Overview
Provides service abstraction, HTTP backend client implementation, and offline mock emulation for the RT letter submission demo module.

## Interface
- `AksiResult`: Response container representing action outcomes, status codes, reference numbers, remaining attempts, lock duration, and helper `terkunci`.
- `PengajuanRtService`: Abstract contract defining operations:
  - `daftarPengajuan()`: Lists all submissions.
  - `detail(int id)`: Gets single submission details.
  - `mintaRevisi(int id, String catatan)`: Submits revision request note.
  - `tolak(int id, String alasan)`: Rejects submission with reason.
  - `sahkanDigital(int id, String pin)`: Authorizes submission digitally with PIN.
  - `setujuiBasah(int id)`: Approves submission for manual physical signing.
- `ApiPengajuanRtService`: HTTP client implementation connecting to the Flask backend `/rt/pengajuan` endpoints.
- `MockPengajuanRtService`: In-memory mock service with simulated dummy data, PIN authorization (PIN `482913`), and lockout after 5 incorrect attempts.

## Invariants
- `ApiPengajuanRtService` injects JWT token headers dynamically via `tokenProvider`.
- `MockPengajuanRtService` enforces a simulated 15-minute lock upon 5 consecutive wrong PIN entries.
- HTTP status 423 is mapped to `terkunci = true` in `AksiResult`.

## Side Effects
- `ApiPengajuanRtService` makes HTTP network calls using `package:http`.
- `MockPengajuanRtService` mutates in-memory mock datasets and attempt counters.

## Verification
- Run: `cd frontend && flutter test`
