# REST API Route Blueprints

## Overview
HTTP request handlers and routing layer for the RTConnect REST API. Implements Flask Blueprints under `/api/v1` managing citizen authentication, letter application workflows, RT administration review queues, TanyaRT conversational RAG queries, push notification tokens, and file downloads.

## Interface
- `auth_routes.py` (`auth_bp`, prefix `/api/v1/auth`):
  - `POST /register`: Public citizen self-registration with NIK and credential hashing.
  - `POST /login`: Public login issuing JWT Bearer tokens and role information.
  - `GET /me`: Fetches profile details for the authenticated user.
  - `PUT/PATCH /me`: Updates resident contact and address details.
  - `POST /signature`, `GET /signature`: Uploads or fetches RT/warga signature assets.
  - `POST /avatar`, `GET /avatar`: Uploads or fetches user profile avatars.
  - `GET /files/<path:storage_key>`: Protected file retrieval for private attachments.
  - `POST /device-token`, `DELETE /device-token`: Registers or deregisters FCM device tokens.
- `letter_routes.py` (`letter_bp`, prefix `/api/v1/letters`):
  - `GET /types`: Catalogs active letter types (`jenis_surat`).
  - `POST /apply`: Submits a new letter request with demographic snapshots and attachments.
  - `GET /my-applications`: Fetches application history for the current resident.
  - `GET /incoming-queue`: RT review queue displaying pending applications.
  - `GET /<int:id>`: Retrieves application detail (restricted to applicant, RT, or admin).
  - `POST /ai-fill`: Extracts form fields from resident conversational prompts.
  - `GET /ai-stats`: Returns performance metrics and resident edit ratios for AI form filling.
  - `GET /my-last-data`: Fetches demographic values from applicant's latest submission for pre-fill.
  - `PUT /<int:id>/resubmit`: Resubmits an application following RT revision requests.
  - `POST /<int:id>/decision`: RT approval or revision rejection with feedback notes.
  - `POST /<int:id>/sign-digital`: PIN-protected RT digital signature overlay and PDF finalization.
  - `POST /<int:id>/confirm-physical`: Confirms offline physical wet signature workflow.
  - `GET /<int:id>/download`: Downloads final generated letter PDF.
  - `GET /<int:id>/download-link`: Generates secure temporary download URLs.
- `chatbot_routes.py` (`chatbot_bp`, prefix `/api/v1/chatbot`):
  - `POST /query`: Evaluates resident query using runtime lexical RAG and topic heuristics.
  - `GET /sessions`: Lists previous chat sessions for current user.
  - `GET /sessions/<int:session_id>/messages`: Fetches chat history for a session.
  - `GET /knowledge`, `POST /knowledge`, `PUT /knowledge/<id>`, `DELETE /knowledge/<id>`: RT/admin CRUD endpoints managing local neighborhood SOP knowledge chunks.
- `notification_routes.py` (`notification_bp`, prefix `/api/v1/notifications`):
  - `GET /`: Lists notifications and unread counters for authenticated user.
  - `PUT /<int:id>/read`: Marks a single notification as read.
  - `PUT /read-all`: Marks all user notifications as read.

## Invariants
- Route namespace: All routes are scoped under the `/api/v1` URL prefix.
- Standard JSON envelope: All success and error responses conform to `{success: bool, message: str, data: any, error: any}`.
- Authorization boundaries: Endpoints verify access through `@jwt_required` and `@roles_accepted('warga', 'rt', 'admin')`; resource details verify tenancy (users may only view their own applications unless assigned RT/admin role).
- Digital signature requirement: `POST /letters/<id>/sign-digital` requires `RT_SIGNING_PIN_HASH` configured in environment; calls return 503 if unconfigured and 400 on PIN mismatch.

## Side Effects
- Mutates database state across `pengajuansurat`, `draftsurat`, `suratfinal`, `notifikasi`, `sesi_chat`, `pesan_chat`, and `ai_fill_log`.
- Dispatches asynchronous or immediate push notifications via Firebase Cloud Messaging.
- Reads and writes binary assets (PDFs, signatures, avatars, attachments) in local storage or S3 bucket.

## Verification
- Run: `cd backend && python test_api.py`
