"""Setup sekali jalan: hubungkan backend RTConnect ke Supabase.

Jalankan dari folder backend:   python setup_supabase.py

Langkah:
  1. Mengisi RT_SIGNING_PIN_HASH (bcrypt dari PIN 123456) di backend/.env bila kosong.
  2. Mencari koneksi database yang berhasil (pooler aws-0/aws-1, direct host,
     dan kandidat password dari SUPABASE_DB_PASSWORD_CANDIDATES) lalu menyimpan
     URL yang benar ke backend/.env.
  3. Menjalankan migrasi SQL tambahan (database/supabase_sql/*.sql).
  4. Mengisi data awal: jenis surat, basis pengetahuan chatbot, akun demo.
  5. Membuat bucket Supabase Storage (S3) bila belum ada.

Aman dijalankan berulang.
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / '.env'
SIGNING_PIN = '123456'


# ---------------------------------------------------------------- .env helpers
def read_env():
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip()
    return values


def set_env(key, value):
    lines = ENV_PATH.read_text(encoding='utf-8').splitlines() if ENV_PATH.exists() else []
    for index, line in enumerate(lines):
        if line.split('=', 1)[0].strip() == key and not line.lstrip().startswith('#'):
            lines[index] = f'{key}={value}'
            break
    else:
        lines.append(f'{key}={value}')
    ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    os.environ[key] = value


# ---------------------------------------------------------------- langkah 1
def ensure_pin_hash():
    if read_env().get('RT_SIGNING_PIN_HASH'):
        print('[OK] RT_SIGNING_PIN_HASH sudah ada.')
        return
    import bcrypt

    pin_hash = bcrypt.hashpw(SIGNING_PIN.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    set_env('RT_SIGNING_PIN_HASH', pin_hash)
    print(f'[+] RT_SIGNING_PIN_HASH dibuat (PIN TTD = {SIGNING_PIN}).')


# ---------------------------------------------------------------- langkah 2
def _candidates(url):
    parsed = urlparse(url)
    ref = (parsed.username or '').split('.', 1)[-1] or 'okmubevurpbgcckoclym'
    region = 'ap-northeast-2'
    host = parsed.hostname or ''
    if '.pooler.supabase.com' in host:
        region = host.split('.')[0].split('-', 2)[-1]
    # Password alternatif (dipisah koma) hanya dibaca dari .env, tidak ditulis di kode.
    extra = os.getenv('SUPABASE_DB_PASSWORD_CANDIDATES', '') or read_env().get('SUPABASE_DB_PASSWORD_CANDIDATES', '')
    passwords = [unquote(parsed.password or '')] + [p.strip() for p in extra.split(',') if p.strip()]
    hosts = [
        (host, parsed.port or 5432, parsed.username),
        (f'aws-0-{region}.pooler.supabase.com', 5432, f'postgres.{ref}'),
        (f'aws-1-{region}.pooler.supabase.com', 5432, f'postgres.{ref}'),
        (f'db.{ref}.supabase.co', 5432, 'postgres'),
    ]
    seen = set()
    for h, port, user in hosts:
        for password in passwords:
            key = (h, port, user, password)
            if h and password and key not in seen:
                seen.add(key)
                yield h, port, user, password


def find_database_url():
    import psycopg

    url = read_env().get('SUPABASE_DB_URL') or os.getenv('SUPABASE_DB_URL')
    if not url:
        sys.exit('[X] SUPABASE_DB_URL belum diisi di backend/.env')

    dbname = urlparse(url).path.lstrip('/') or 'postgres'
    errors = []
    for host, port, user, password in _candidates(url):
        try:
            conn = psycopg.connect(
                host=host, port=port, user=user, password=password,
                dbname=dbname, sslmode='require', connect_timeout=10,
            )
            conn.close()
        except Exception as error:  # coba kandidat berikutnya
            errors.append(f'  - {user}@{host}: {str(error).strip().splitlines()[0]}')
            continue
        good = f'postgresql://{user}:{quote(password, safe="")}@{host}:{port}/{dbname}'
        if good != url:
            set_env('SUPABASE_DB_URL', good)
            print(f'[+] Koneksi berhasil lewat {host}; URL di .env diperbarui.')
        else:
            print(f'[OK] Koneksi database berhasil ({host}).')
        os.environ['SUPABASE_DB_URL'] = good
        return

    print('[X] Tidak bisa terhubung ke database Supabase. Hasil percobaan:')
    print('\n'.join(errors))
    print('\nPeriksa:')
    print('  - "password authentication failed": password database salah. Reset di Supabase >')
    print('    Project Settings > Database > Reset database password, lalu isi di SUPABASE_DB_URL.')
    print('  - "Tenant or user not found": salin URL dari Supabase > tombol "Connect" > Session pooler.')
    print('  - timeout / could not translate host: cek internet; jaringan kampus kadang memblokir port 5432.')
    sys.exit(1)


# ---------------------------------------------------------------- langkah 5
def ensure_bucket():
    from config import Config

    if Config.STORAGE_BACKEND != 's3':
        print('[i] STORAGE_BACKEND bukan s3, bucket dilewati.')
        return
    from services.file_storage import _s3_client

    client = _s3_client()
    bucket = Config.S3_BUCKET
    try:
        client.head_bucket(Bucket=bucket)
        print(f'[OK] Bucket storage "{bucket}" sudah ada.')
        return
    except Exception as error:
        code = str(getattr(error, 'response', {}).get('Error', {}).get('Code', ''))
        if code not in {'404', 'NoSuchBucket', 'NotFound'}:
            print(f'[!] Tidak bisa memeriksa bucket "{bucket}": {error}')
            print('    Cek S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY / S3_ENDPOINT_URL di .env.')
            return
    try:
        client.create_bucket(Bucket=bucket)
        print(f'[+] Bucket storage "{bucket}" dibuat (private).')
    except Exception as error:
        print(f'[!] Gagal membuat bucket "{bucket}": {error}')
        print('    Buat manual: Supabase > Storage > New bucket > nama "rtconnect-files", Public OFF.')


def main():
    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))
    if not ENV_PATH.exists():
        sys.exit(f'[X] {ENV_PATH} tidak ditemukan.')

    ensure_pin_hash()
    find_database_url()

    # Import setelah .env final, karena config.py & db.py membaca .env saat diimport.
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH, override=True)
    from database.migrate import migrate
    from database.seed import seed_database

    migrate()
    seed_database(include_demo_users=True)
    ensure_bucket()

    print('\n=== SETUP SUPABASE SELESAI ===')
    print('Akun Ketua RT : rt@example.test        / LocalTestOnly#2026')
    print('Akun Warga    : resident@example.test  / LocalTestOnly#2026')
    print(f'PIN TTD digital: {SIGNING_PIN}')


if __name__ == '__main__':
    main()
