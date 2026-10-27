# Global Deployment Guide

RTConnect can be made publicly reachable from mobile devices and browsers by deploying the Flask API behind HTTPS and building Flutter clients with that API URL. The app remains a **single-community deployment**: one database and one RT/RW configuration per deployment; it is not multi-tenant.

## 1. Provision services

Choose a container host with a public HTTPS endpoint, a managed MySQL 8.4 database, and private S3-compatible object storage. Keep MySQL accessible only to the API and migration jobs. Place the API near the database to avoid adding database round-trip latency. Use the host's domain/TLS integration or a custom domain with managed TLS.

Configure the bucket as private, enable provider-side encryption and versioning where available, and give the API only the required bucket access. The API serves uploads and PDFs after checking the user's authorization; do not make the bucket public.

## 2. Production environment

Set these values in the hosting platform's secret/environment settings. Do not commit a production `.env` file.

| Variable | Purpose |
|---|---|
| `APP_ENV=production` | Enables production validation and disables the Flask debugger |
| `JWT_SECRET` | Random secret of at least 32 characters; keep the same value across every worker/replica and across restarts; rotation invalidates all sessions |
| `RT_SIGNING_PIN_HASH` | Bcrypt hash produced with `python -m database.hash_rt_pin` |
| `MYSQL_SSL_CA` | Path inside the container to the managed database CA PEM file |
| `MYSQL_SSL_MODE=required` | Require TLS; the configured CA is used to verify the database certificate and hostname |
| `MYSQL_URL` or `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` | Runtime database connection |
| `MIGRATION_DATABASE_URL` | Optional higher-privilege connection used only by the release migration command |
| `MIGRATION_MYSQL_SSL_CA` | Optional CA path when the migration database uses a different certificate |
| `STORAGE_BACKEND=s3` | Use persistent object storage rather than container-local files |
| `S3_BUCKET`, `S3_REGION` | Private bucket name and region |
| `S3_ENDPOINT_URL` | Optional endpoint for an S3-compatible provider such as R2 or MinIO |
| `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Use platform workload identity when available; otherwise store these as secrets |
| `CORS_ORIGINS` | Comma-separated exact HTTPS origins for Flutter Web, such as `https://app.example.com` |
| `RT_WHATSAPP_NUMBER` | International digits only, 8–15 digits, for example `6281234567890` |
| `RT_NAME`, `RT_AREA` | Display metadata for this community |
| `RT_NUMBER`, `RW_NUMBER`, `RT_LETTER_CODE` | RT/RW numbers and official letter number prefix |
| `RT_LOCATION_LINE_2`, `RT_LOCATION_LINE_3`, `RT_SIGNING_LOCATION` | Address and signing place shown on issued PDFs |

Production startup deliberately fails if the JWT secret, PIN hash, S3 bucket, database CA, Web CORS origin, or WhatsApp number is missing. CORS does not apply to native Android/iOS requests, but the web origin must be listed exactly; do not use `*`.

Generate secrets in a secure terminal, then copy them directly into the platform secret manager:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -m database.hash_rt_pin
```

Use a long, unique database password and separate runtime and migration database users where the host supports it. The runtime user needs application DML privileges; the migration user needs schema DDL privileges.

## 3. Database migration and initial account

Back up any existing database before changing it. Run the migration as a one-off release command with the migration connection configured:

```sh
python -m database.migrate
python -m database.seed
```

The migration aligns the old signature column, adds the missing QR verification column, and normalizes old local file keys. Migrations are not run when the API starts. `seed` adds master letter types and knowledge chunks; it does not create user accounts. Demo accounts are blocked in production.

Create the first RT account in a protected one-off shell after the migration:

```sh
python -m database.create_rt_user
```

The command prompts for the RT's profile, password, and signature image. The signature image is required before production can issue a digitally signed PDF. Do not expose this command through a public HTTP endpoint. Residents can then register through the app.

### Existing local uploads

For existing deployments, keep the old `backend/uploads` volume available while moving files. After running the database migration, run a one-off copy job with `STORAGE_BACKEND=s3`, the bucket credentials, and the old upload volume mounted at the configured upload directory:

```sh
python -m database.sync_local_uploads_to_s3
```

Review the command's missing-file output before switching traffic. New deployments with no existing uploads can start directly with S3 storage.

## 4. Deploy the API

Build from the `backend/` directory using `backend/Dockerfile`. The image runs Gunicorn as a non-root user and does not include `.env` or the repository's local signature/upload files. Configure the platform's start command from the image and expose its assigned `PORT`.

Run `python -m database.migrate` as a release/one-off command before shifting traffic to a new image. Configure the production environment above, attach the database CA file at `MYSQL_SSL_CA`, and set the API's public custom domain. Check:

```text
https://api.example.com/api/v1/health
```

A healthy response means the API can connect to MySQL. The endpoint does not reveal connection details on failure.

### PaaS deployment (Procfile)

For platforms using buildpacks with a Procfile (such as Railway or Render), configure the service's **Root Directory** to `backend/`. The backend directory contains the single active `backend/Procfile`:

```text
release: python -m database.migrate
web: gunicorn --workers 2 --threads 4 --timeout 60 -b 0.0.0.0:$PORT app:app
```

The `release` command executes database migrations before incoming traffic shifts to the new version, and the `web` process runs Gunicorn bound to the platform's assigned `$PORT`.

## 5. Publish Flutter clients

The API URL must include `/api/v1` and use HTTPS:

```sh
flutter pub get
flutter build web --release --dart-define=API_BASE_URL=https://api.example.com/api/v1
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.example.com/api/v1
```

Host the contents of `build/web` over HTTPS and add that exact origin to `CORS_ORIGINS`. The Android release manifest blocks cleartext HTTP; only debug builds allow it.

For automated Flutter Web builds, add this GitHub repository variable:

- `API_BASE_URL=https://api.example.com/api/v1`
- `RT_AREA=RT 032 / RW 08 Griya Taman Asri` (optional; shown in the app and defaulted in source)

The workflow uploads a `rtconnect-web-release` artifact for static hosting. For automated Android releases, also add this repository variable:

- `ANDROID_RELEASE_ENABLED=true`

Then add these repository secrets:

- `ANDROID_KEYSTORE_BASE64`: base64-encoded Play upload keystore
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`
- `ANDROID_STORE_PASSWORD`

The workflow signs APK and AAB artifacts with that upload key. To create one locally, use `keytool -genkeypair` and keep the keystore/passwords outside Git. Never reuse a debug keystore for a public release.

Create a dedicated Play upload key once:

```sh
keytool -genkeypair -v -keystore rtconnect-upload.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias rtconnect-upload
base64 -w 0 rtconnect-upload.jks
```

In Windows PowerShell, encode it with `[Convert]::ToBase64String([IO.File]::ReadAllBytes('rtconnect-upload.jks'))`. Store the keystore and passwords in a secure backup outside this repository.

Increment `version` and build number in `pubspec.yaml` before each store release. Apple App Store distribution also needs an Apple signing certificate/profile and is completed with Xcode on macOS.

## 6. Operational checks

- Schedule database backups and periodically verify that a backup can be restored.
- Monitor `/api/v1/health`, API error rates, storage failures, and database capacity.
- Keep TLS enabled for the public API and database. Rotate JWT, database, bucket, and signing-PIN secrets if they are exposed; JWT rotation signs out all users.
- Treat NIK, phone numbers, addresses, chat history, signatures, and issued PDFs as personal data. Define access, retention, and deletion rules before onboarding residents.
- Apply request throttling at the hosting proxy/WAF for login, registration, and PIN-protected signing before opening the API to unrestricted traffic.
- The signing flow currently places a signature image into the PDF; it does not cryptographically sign the PDF or provide an integrity-verification chain.
