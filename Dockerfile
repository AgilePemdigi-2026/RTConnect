# =====================================================================
# RTConnect - satu container untuk Coolify (Flutter Web + Flask API)
#   https://<nama-app>.caiis.ai.id/          -> aplikasi Flutter Web
#   https://<nama-app>.caiis.ai.id/api/v1/   -> REST API Flask
# Satu domain = tidak perlu atur alamat API terpisah di Flutter.
# =====================================================================

# ---------- Tahap 1: build Flutter Web ----------
FROM ghcr.io/cirruslabs/flutter:stable AS web
WORKDIR /src
COPY frontend/pubspec.yaml frontend/pubspec.lock ./
RUN flutter pub get
COPY frontend/ ./
# API_BASE_URL sengaja dikosongkan: versi web otomatis memakai <domain>/api/v1
RUN flutter build web --release

# ---------- Tahap 2: backend Flask + hasil build web ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=5000 \
    WEB_BUILD_DIR=/app/web

WORKDIR /app
RUN groupadd --system rtconnect && useradd --system --gid rtconnect --home-dir /app rtconnect

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=rtconnect:rtconnect backend/ ./
COPY --from=web --chown=rtconnect:rtconnect /src/build/web ./web
RUN mkdir -p /app/uploads/signatures /app/uploads/attachments /app/uploads/generated_letters \
    && chown -R rtconnect:rtconnect /app

USER rtconnect
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.getenv('PORT','5000'), timeout=8)" || exit 1

# Timeout 180 dtk: panggilan AI (Gemini / LLM server kampus) bisa lebih dari 60 dtk.
# RUN_MIGRATIONS=true -> jalankan migrasi database sebelum server start.
CMD ["sh", "-c", "if [ \"$RUN_MIGRATIONS\" = \"true\" ]; then python -m database.migrate; fi; exec gunicorn --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout ${GUNICORN_TIMEOUT:-180} --bind 0.0.0.0:${PORT:-5000} app:app"]
