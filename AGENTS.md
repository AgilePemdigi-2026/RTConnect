# AGENTS.md

## Layout
- `frontend/` is the only Flutter project root (`pubspec.yaml`, platform folders, `lib/`, `test/`). Do not recreate `lib/` or `test/` at the repository root.
- `backend/` is the Flask REST API and MySQL schema/migrations.
- `frontend/lib/features/pengajuan_rt/` is a legacy standalone demo (`MockPengajuanRtService`, endpoints `/api/rt/pengajuan`). The live UI is `frontend/lib/features/letters/` against `/api/v1/letters`.

## Commands
- Dev stack: create `.env` at the repo root with `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` (Compose refuses to start without them), then `docker compose up --build`. API: `http://localhost:5000`; health: `/api/v1/health`. Docs mention `.env.example`, but it is not checked in.
- Compose runs `python -m database.migrate` and `python -m database.seed` before Gunicorn; production never auto-migrates.
- Backend modules use top-level imports, so run from `backend/`: `python -m database.migrate`, `python -m database.seed`, `python -m database.create_rt_user`, `python -m database.hash_rt_pin`.
- Local API without Docker: `cd backend && pip install -r requirements.txt && python app.py`.
- Backend integration suite: `cd backend && python test_api.py` (plain script, not pytest). It needs MySQL, `SEED_DEMO_USERS=true python -m database.seed`, demo users `rt@example.test` / `resident@example.test` (password `LocalTestOnly#2026`), and `RT_SIGNING_PIN_HASH` set to a bcrypt hash of `123456`. It writes to the database; use a disposable one.
- Flutter: `cd frontend && flutter pub get && flutter analyze && flutter test`. Single test: `flutter test test/widget/rt_status_badge_test.dart`. Web build: `flutter build web --release --dart-define=API_BASE_URL=https://api.example.com/api/v1`.

## Backend
- All blueprints mount under `/api/v1`; roles are `warga`, `rt`, `admin` (docs mentioning `ketua_rt` are stale). JSON envelope: `{success, message, data, error}`.
- Runtime chatbot is `services/rag_service.py` (lexical TF cosine + simple Indonesian stemming). `backend/chatbot/` is offline training/evaluation code requiring sentence-transformers, rank_bm25, and numpy, which are not in `requirements.txt`; do not import it from the API.
- `APP_ENV=production` makes `config.py` fail fast (JWT secret, PIN hash, S3, database CA, CORS, WhatsApp). Do not use it for local work.
- Digital signing overlays a signature image into the PDF; it is not cryptographic. If `RT_SIGNING_PIN_HASH` is unset, `sign-digital` returns 503.
- Uploads are private: local `backend/uploads` or S3 via `STORAGE_BACKEND`.

## Frontend
- `API_BASE_URL` must include `/api/v1`; it is read via dart-define in `lib/core/constants/app_constants.dart` (Android debug defaults to `10.0.2.2:5000`). Release builds reject non-HTTPS API URLs.
- Riverpod + go_router. Register screens in `lib/core/router/`, API paths in `lib/core/network/api_endpoints.dart`, and call through `ApiClient`. Reuse `lib/shared/widgets/rt_*` and `lib/core/theme`; UI copy is Indonesian.

## Docs and secrets
- Trust `backend/README.md` and `DEPLOYMENT.md`. `frontend/README.md` is stale (describes an all-root layout and Gemini/embedding-based RAG).
- No CI workflows are checked in despite README references.
- Only `frontend/.gitignore` exists; root `.env` and `backend/.env` are not ignored. Keep secrets out of commits.
