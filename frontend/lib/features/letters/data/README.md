# Letters Data

## Overview
Provides network access, data serialization, and file upload services for the primary letter administration lifecycle (pengajuan surat), including AI-assisted form filling, digital signature authorization, physical approval confirmation, and status review.

## Interface
- `LetterRepository`:
  - `getLetterTypes()`: Fetches available letter templates and categories.
  - `applyLetter(...)`: Submits a new citizen letter application with applicant details, signing method, and optional attachment or AI telemetry metadata.
  - `getMyLastApplicantData()`: Retrieves previously stored citizen demographic data to prefill forms.
  - `aiFill(String pesan, {List<String> riwayat})`: Queries generative AI service to extract structured form fields from unstructured citizen prose.
  - `getMyApplications()`: Retrieves historical and in-progress applications submitted by the current citizen.
  - `getIncomingQueue()`: Fetches pending letter requests requiring RT official review.
  - `getApplicationDetail(int id)`: Retrieves detailed information, status logs, and PDF URLs for a specific letter.
  - `resubmitLetter(int id, String keperluan, {Map<String, String>? dataPemohon})`: Resubmits an application after addressal of revision notes.
  - `submitDecision(int id, String action, String catatan)`: Posts RT official decisions (`setuju`, `revisi`, `tolak`).
  - `signDigital(int id, String pin)`: Authorizes digital signing of a letter via RT PIN.
  - `confirmPhysical(int id)`: Confirms that a physically signed letter is finalized and ready for pickup.

## Invariants
- When an attachment file path is provided, submissions are encoded as `multipart/form-data`; otherwise standard JSON payload is sent.
- `aiFill` uses an extended HTTP receive timeout of 90 seconds to accommodate LLM inference latency.
- Demographic fields in `dataPemohon` must follow established format conventions (dates in `YYYY-MM-DD`).

## Side Effects
- Makes HTTP GET, POST, and PUT calls across `/api/v1/letters/*` endpoints.
- Reads attachment files from device storage via `MultipartFile.fromFile`.

## Verification
- Run: `cd frontend && flutter test`
