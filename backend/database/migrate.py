"""Apply the checked-in MySQL schema and compatibility migrations."""

from pathlib import Path

from database.db import get_connection


MIGRATION_TABLE = 'rtconnect_schema_migrations'


def _columns(cursor, table_name):
    cursor.execute(
        """SELECT COLUMN_NAME FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s""",
        (table_name,),
    )
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


def _tables(cursor):
    cursor.execute('SHOW TABLES')
    return {next(iter(row.values())) for row in cursor.fetchall()}


def _apply_initial_schema(cursor):
    schema_path = Path(__file__).with_name('schema.sql')
    schema = schema_path.read_text(encoding='utf-8')
    for statement in schema.split(';'):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def _apply_compatibility_migration(cursor):
    tables = _tables(cursor)
    if 'users' in tables:
        user_columns = _columns(cursor, 'users')
        if 'tanda_tangan_url' not in user_columns and 'tanda_tangan_digital' in user_columns:
            cursor.execute(
                "ALTER TABLE users CHANGE COLUMN tanda_tangan_digital tanda_tangan_url VARCHAR(512) NULL"
            )
        elif 'tanda_tangan_url' not in user_columns:
            cursor.execute(
                'ALTER TABLE users ADD COLUMN tanda_tangan_url VARCHAR(512) NULL'
            )
        elif 'tanda_tangan_digital' in user_columns:
            cursor.execute(
                "UPDATE users SET tanda_tangan_url = tanda_tangan_digital "
                "WHERE tanda_tangan_url IS NULL AND tanda_tangan_digital IS NOT NULL"
            )

    if 'surat_final' in tables and 'qr_verification_token' not in _columns(cursor, 'surat_final'):
        cursor.execute(
            'ALTER TABLE surat_final ADD COLUMN qr_verification_token VARCHAR(128) NULL UNIQUE'
        )

    # Older releases stored paths relative to the backend directory, including
    # an unnecessary leading "uploads/". Canonical keys are relative to the
    # storage root so they work with both local disk and private object storage.
    if 'users' in tables:
        cursor.execute(
            "UPDATE users SET tanda_tangan_url = SUBSTRING(tanda_tangan_url, 9) "
            "WHERE tanda_tangan_url LIKE 'uploads/%'"
        )
    if 'pengajuan_surat' in tables:
        cursor.execute(
            "UPDATE pengajuan_surat SET berkas_lampiran_url = SUBSTRING(berkas_lampiran_url, 9) "
            "WHERE berkas_lampiran_url LIKE 'uploads/%'"
        )
    if 'surat_final' in tables:
        cursor.execute(
            "UPDATE surat_final SET file_pdf_path = SUBSTRING(file_pdf_path, 9) "
            "WHERE file_pdf_path LIKE 'uploads/%'"
        )


def migrate():
    connection = get_connection(migration=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS `{MIGRATION_TABLE}` (
                    version INT PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB"""
            )
            cursor.execute(f'SELECT COALESCE(MAX(version), 0) AS version FROM `{MIGRATION_TABLE}`')
            version = cursor.fetchone()['version']

            if version < 1:
                _apply_initial_schema(cursor)
                cursor.execute(f'INSERT INTO `{MIGRATION_TABLE}` (version) VALUES (1)')
                version = 1

            if version < 2:
                _apply_compatibility_migration(cursor)
                cursor.execute(f'INSERT INTO `{MIGRATION_TABLE}` (version) VALUES (2)')

        print('Database migrations completed.')
    finally:
        connection.close()


if __name__ == '__main__':
    migrate()
