"""Koneksi PostgreSQL (Supabase) untuk backend RTConnect.

API tetap sama dengan versi MySQL lama: query_all, query_one, execute.
Tambahan: execute_returning (untuk INSERT ... RETURNING) dan transaction().

Variabel .env yang dibaca (salah satu):
    SUPABASE_DB_URL / DATABASE_URL / POSTGRES_URL
Contoh (Session pooler, dari Dashboard Supabase > tombol "Connect"):
    SUPABASE_DB_URL=postgresql://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:5432/postgres
"""

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_BACKEND_DIR = Path(__file__).resolve().parent.parent
# backend/.env adalah konfigurasi utama; supabase_connect/.env hanya cadangan.
for _env in (
    _BACKEND_DIR / '.env',
    _BACKEND_DIR.parent / '.env',
    _BACKEND_DIR / 'supabase_connect' / '.env',
):
    load_dotenv(_env)
load_dotenv()

IntegrityError = psycopg.IntegrityError
UniqueViolation = psycopg.errors.UniqueViolation

_pool = None
_pool_lock = threading.Lock()


def _database_url():
    url = (os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
           or os.getenv('POSTGRES_URL'))
    if not url:
        raise RuntimeError(
            'SUPABASE_DB_URL belum diisi di .env. Ambil dari Dashboard Supabase > tombol '
            '"Connect" > Session pooler > URI, lalu ganti [YOUR-PASSWORD] dengan password database.'
        )
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return url


def _conninfo():
    url = _database_url()
    info = conninfo_to_dict(url)
    host = urlparse(url).hostname or ''
    if 'sslmode' not in info and host not in {'localhost', '127.0.0.1', '::1'}:
        info['sslmode'] = 'require'  # Supabase mewajibkan TLS
    return make_conninfo(**info)


def _configure(conn):
    # Zona waktu sesi menentukan nilai CURRENT_TIMESTAMP pada kolom "timestamp without time zone".
    conn.execute("SELECT set_config('TimeZone', %s, false)", (os.getenv('DB_TIMEZONE', 'Asia/Jakarta'),))


def get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                pool = ConnectionPool(
                    _conninfo(),
                    min_size=1,
                    max_size=int(os.getenv('DB_POOL_MAX', '5')),
                    max_idle=300,
                    kwargs={
                        'row_factory': dict_row,
                        'autocommit': True,
                        'prepare_threshold': None,  # aman untuk pooler Supabase
                        'connect_timeout': 15,
                    },
                    configure=_configure,
                    check=ConnectionPool.check_connection,
                    open=False,
                )
                pool.open(wait=True, timeout=30)
                _pool = pool
    return _pool


def close_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None


def query_all(sql, params=None):
    with get_pool().connection() as conn:
        return conn.execute(sql, params or ()).fetchall()


def query_one(sql, params=None):
    with get_pool().connection() as conn:
        return conn.execute(sql, params or ()).fetchone()


def execute(sql, params=None):
    """Jalankan INSERT/UPDATE/DELETE. Mengembalikan jumlah baris yang terpengaruh."""
    with get_pool().connection() as conn:
        return conn.execute(sql, params or ()).rowcount


def execute_returning(sql, params=None):
    """Jalankan statement dengan RETURNING dan kembalikan baris pertama (dict) atau None."""
    with get_pool().connection() as conn:
        return conn.execute(sql, params or ()).fetchone()


@contextmanager
def transaction():
    """Transaksi atomik. Yield cursor (baris berupa dict); rollback otomatis jika error.

        with transaction() as cur:
            cur.execute("INSERT ... RETURNING id", (...))
            new_id = cur.fetchone()['id']
    """
    with get_pool().connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                yield cur