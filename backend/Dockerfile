FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=5000

WORKDIR /app
RUN groupadd --system rtconnect && useradd --system --gid rtconnect --home-dir /app rtconnect

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=rtconnect:rtconnect . .
RUN mkdir -p /app/uploads/signatures /app/uploads/attachments /app/uploads/generated_letters \
    && chown -R rtconnect:rtconnect /app

USER rtconnect
EXPOSE 5000
CMD ["sh", "-c", "exec gunicorn --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 60 --bind 0.0.0.0:${PORT:-5000} app:app"]
