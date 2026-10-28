# RTConnect — Backend REST API

Flask REST API for RTConnect. Letter drafts are built from a deterministic template. Tanya RT ranks knowledge chunks with lexical cosine similarity, simple Indonesian stemming, topic/action boosts, and a scope guard; it does not call an LLM or use embeddings. Returned retrieval scores are heuristic, not model confidence. `database/seed.py` imports the 20 public government references from `chatbot/dataset/knowledgebase.jsonl`.

## Stack

- Python 3.12+, Flask, Gunicorn
- MySQL 8.4+, PyMySQL with TLS support
- JWT HS256 with one-day expiry; bcrypt password and RT signing-PIN hashes
- Private local storage for development or private S3-compatible object storage for production
- ReportLab PDF generation; displayed signature images are not cryptographic PDF signatures

JWT signing uses one stable secret shared by every API worker and replica. Local development has a fixed development-only fallback so Gunicorn workers can verify each other's tokens. Production has no fallback: configure the same randomly generated `JWT_SECRET` for every process, keep it stable across restarts, and rotate it only when you intend to sign out all users.

## Important files

- `app.py`: Flask application and health endpoint
- `config.py`: environment-based configuration and production validation
- `database/schema.sql`: canonical schema
- `database/migrate.py`: versioned schema migration, including upgrades from the previous column names
- `database/seed.py`: idempotent master data; demo accounts are disabled by default
- `database/create_rt_user.py`: interactive first RT account setup
- `database/hash_rt_pin.py`: interactively generate `RT_SIGNING_PIN_HASH`
- `database/sync_local_uploads_to_s3.py`: copy existing local uploads to the configured private bucket
- `services/file_storage.py`: content validation and local/S3-compatible storage
- `services/rag_service.py`: runtime chatbot ranking and answer/fallback result
- `services/chatbot_rules.py`: topic/action rules and scope guard shared by runtime
- `chatbot/evaluate_runtime.py`: runtime retrieval evaluation without MySQL
- `test_api.py`: MySQL-backed API integration suite

## Local setup

From the repository root, copy `.env.example` to `.env`, change the local passwords, then run:

```powershell
docker compose up --build
```

The API is available at `http://localhost:5000`; `GET /api/v1/health` reports database availability. Create the first RT account in a second terminal:

```powershell
docker compose exec api python -m database.create_rt_user
```

Then register a resident in the Flutter app. To allow digital signing locally, generate a PIN hash with `docker compose exec api python -m database.hash_rt_pin`, put the hash in `.env` as `RT_SIGNING_PIN_HASH`, and restart the API. Never use demo credentials in a public environment.

## Production

Do not run the Flask development server in production. Deploy the Docker image behind an HTTPS-enabled container host, use a managed MySQL database with a trusted CA certificate, and configure a private S3-compatible bucket. The application process does not run migrations or seed accounts at startup.

Run `python -m database.migrate` once as a release command using a migration database credential. Run `python -m database.seed` for master letter types and knowledge content. Create the initial RT account with `python -m database.create_rt_user` in a protected one-off shell. See [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for the production environment and Flutter build steps.

Demo users can only be seeded when `SEED_DEMO_USERS=true` outside production. Production startup rejects that setting.

## API endpoints

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

The GitHub Actions workflow compiles the backend Python files and analyzes Flutter code. It can build the web release artifact and signed Android APK/AAB when the repository variables and signing secrets are configured. The MySQL-backed API integration script is available for manual use in an isolated test database.

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
```
