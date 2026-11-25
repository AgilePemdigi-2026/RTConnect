# RTConnect Backend Blueprint

## System Overview
The RTConnect backend is a modular Flask REST API serving administrative workflows for Indonesian neighborhood units (Rukun Tetangga / RT). It manages citizen registration, authentication, official administrative letter drafting, digital signing with PIN verification, incoming review queues for RT administrators, push notifications, and the TanyaRT resident conversational assistant.

TanyaRT runtime uses lexical cosine similarity, simple Indonesian stemming, topic/action boosts, and scope guards without relying on external LLMs or vector databases. Letter drafts are synthesized deterministically from structured templates, while ReportLab renders branded official PDF documents with QR verification codes.

### Stack
- Python 3.12+, Flask 3.x, Gunicorn WSGI
- PostgreSQL 14+ (Supabase) via `psycopg` and `psycopg_pool`, with legacy MySQL compatibility
- JWT HS256 authentication with 1-day expiration and bcrypt hashing for passwords and RT signing PINs
- Dual-mode private storage: local filesystem (`backend/uploads`) for development or S3-compatible buckets for production
- ReportLab PDF generation for official letter issuance
- Firebase Admin SDK for FCM mobile push notifications

JWT signing requires a stable secret shared across all workers. In local development, a fixed development fallback is available. Production strictly requires an explicitly configured, high-entropy `JWT_SECRET`.

## Local Interface & Invariants
Direct entrypoints and configuration modules located in the `backend/` root directory:
- `app.py`: Flask application factory (`create_app()`) registering blueprints, error handlers, and `/api/v1/health`.
- `config.py`: Environment configuration class (`Config`) validating required secrets, database credentials, and production constraints.
- `test_api.py`: Comprehensive API integration test suite covering authentication, letter lifecycle, and role permissions.
- `run_bdd.py`: CLI test runner executing Behave BDD acceptance features with custom path and tag filtering.
- `setup_supabase.py`: Automated setup script configuring remote Supabase storage buckets and database connections.
- `evaluate_runtime.py`: Offline evaluation script measuring runtime retrieval ranking without requiring database connectivity.
- `regresi_retrieval_offline.py` & `bandingkan_model.py`: Benchmark scripts evaluating lexical vs embedding retrieval models.
- `Dockerfile` & `Procfile`: Containerization and process definitions for container platforms and Gunicorn deployment.

## Subdirectories & System Boundaries
- [chatbot](./chatbot/README.md): Offline evaluation pipeline, dense embeddings, benchmark datasets, and linguistic rule research for TanyaRT.
- [database](./database/README.md): PostgreSQL/Supabase connection pooling (`psycopg_pool`), schema migrations, and master data seeding scripts.
- [features](./features/README.md): Gherkin BDD scenario suites (`sprint1`, `sprint2`) and Behave execution harness (`environment.py`).
- [middleware](./middleware/README.md): Request interception middleware enforcing JWT Bearer token authentication and Role-Based Access Control (`warga`, `rt`, `admin`).
- [routes](./routes/README.md): Flask REST API route blueprints mounted under `/api/v1` (`auth`, `letters`, `chatbot`, `notifications`).
- [services](./services/README.md): Core business logic services, PDF letter compilation, lexical RAG chatbot, AI form parsing, and notification handlers.
- [supabase_connect](./supabase_connect/README.md): PostgREST client abstraction and Repository pattern implementations for Supabase tables.

## Global Invariants
- API Envelope: All `/api/v1` endpoints consistently respond with JSON envelope format `{ "success": bool, "message": str, "data": any, "error": any }`.
- Role-Based Access: Three canonical roles are recognized: `warga`, `rt`, and `admin`. Requests without requisite permissions return HTTP 403 `FORBIDDEN`.
- Production Guardrails: `APP_ENV=production` enforces fast failure on missing `JWT_SECRET`, unconfigured `RT_SIGNING_PIN_HASH`, missing S3 bucket configuration, or enabled demo seeding flags (`SEED_DEMO_USERS=true`).
- Separation of Concerns: The production runtime API must never import heavy offline ML dependencies from `backend/chatbot/`.

## Global Side Effects
- Relational Database: State mutations across citizen accounts, letter applications, audit logs, and notification records.
- Storage Assets: File creation and deletion for uploaded applicant identity cards, signatures, and compiled letter PDFs.
- External Integrations: Dispatches push notifications to Firebase Cloud Messaging (FCM) and outbound requests to Google Gemini (when AI form-filling is used).

## Local Setup

From the repository root, copy `.env.example` to `.env`, change the local passwords, then run:

```powershell
docker compose up --build
```

The API is available at `http://localhost:5000`; `GET /api/v1/health` reports database availability. Create the first RT account in a second terminal:

```powershell
docker compose exec api python -m database.create_rt_user
```

Then register a resident in the Flutter app. To allow digital signing locally, generate a PIN hash with `docker compose exec api python -m database.hash_rt_pin`, put the hash in `.env` as `RT_SIGNING_PIN_HASH`, and restart the API. Never use demo credentials in a public environment.

## Production Deployment

Do not run the Flask development server in production. Deploy the Docker image behind an HTTPS-enabled container host, use a managed PostgreSQL/Supabase database with a trusted CA certificate, and configure a private S3-compatible bucket. The application process does not run migrations or seed accounts at startup.

Run `python -m database.migrate` once as a release command using a migration database credential. Run `python -m database.seed` for master letter types and knowledge content. Create the initial RT account with `python -m database.create_rt_user` in a protected one-off shell. See [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for the production environment and Flutter build steps.

Demo users can only be seeded when `SEED_DEMO_USERS=true` outside production. Production startup rejects that setting.

## API Endpoints

| Method | Path | Access |
|---|---|---|
| POST | `/api/v1/auth/register` | Public resident registration |
| POST | `/api/v1/auth/login` | Public |
| GET | `/api/v1/auth/me` | Authenticated |
| GET | `/api/v1/letters/types` | Authenticated |
| POST | `/api/v1/letters/apply` | Resident |
| GET | `/api/v1/letters/my-applications` | Resident |
| GET | `/api/v1/letters/incoming-queue` | RT/admin |
| GET | `/api/v1/letters/:id` | Owner, RT, or admin |
| PUT | `/api/v1/letters/:id/resubmit` | Owner resident |
| POST | `/api/v1/letters/:id/decision` | RT/admin |
| POST | `/api/v1/letters/:id/sign-digital` | RT/admin |
| POST | `/api/v1/letters/:id/confirm-physical` | RT/admin |
| GET | `/api/v1/letters/:id/download` | Owner, RT, or admin |
| POST | `/api/v1/chatbot/query` | Resident |
| GET | `/api/v1/notifications` | Authenticated |

## Behavior-Driven Development (BDD)

Skenario pengujian BDD berformat Gherkin (`.gherkin`) yang diselaraskan dengan GitHub Issues dikelola dalam folder `features/`:

```powershell
# Menjalankan seluruh skenario BDD
cd backend
python run_bdd.py

# Menjalankan skenario per sprint atau issue tertentu
python run_bdd.py --tags=@sprint1
python run_bdd.py --tags=@issue-9
python run_bdd.py --tags=@issue-10
python run_bdd.py --tags=@issue-11

# Sprint 2: tinjau pengajuan RT, PIN & nomor surat, generative document AI, revisi biodata
python run_bdd.py features/sprint2
python run_bdd.py --tags=@sprint2
```

## System Verification
- Run: `cd backend && python test_api.py`
