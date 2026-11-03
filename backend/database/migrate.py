"""Terapkan SQL tambahan RTConnect ke database Supabase.

    cd backend
    python -m database.migrate

Aman dijalankan berulang (semua statement idempotent).
"""

from pathlib import Path

from database.db import close_pool, get_pool

SQL_DIR = Path(__file__).with_name('supabase_sql')
FILES = ('001_enums.sql', '002_extensions.sql', '003_data_pemohon.sql')


def migrate():
    pool = get_pool()
    for name in FILES:
        script = (SQL_DIR / name).read_text(encoding='utf-8')
        with pool.connection() as conn:
            conn.execute(script)
        print(f'[OK] {name}')
    print('Migrasi Supabase selesai.')
    close_pool()


if __name__ == '__main__':
    migrate()