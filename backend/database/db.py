import os
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv

import pymysql
from pymysql.cursors import DictCursor

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, '.env'))
load_dotenv(os.path.join(os.path.dirname(_BASE_DIR), '.env'))
load_dotenv()


def _connection_options(migration=False):
    database_url = os.getenv('MIGRATION_DATABASE_URL') if migration else None
    database_url = database_url or (os.getenv('MYSQL_URL') or os.getenv('DATABASE_URL'))
    if database_url and database_url.startswith(('mysql://', 'mysql+pymysql://')):
        parsed = urlparse(database_url)
        options = {
            'host': parsed.hostname or '127.0.0.1',
            'port': parsed.port or 3306,
            'user': unquote(parsed.username or 'rtconnect'),
            'password': unquote(
                parsed.password
                or os.getenv('MYSQLPASSWORD')
                or os.getenv('MYSQL_PASSWORD')
                or os.getenv('DB_PASSWORD', '')
            ),
            'database': unquote(parsed.path.lstrip('/')) or 'rtconnect_db',
        }
    else:
        options = {
            'host': os.getenv('MYSQLHOST') or os.getenv('MYSQL_HOST') or os.getenv('DB_HOST', '127.0.0.1'),
            'port': int(os.getenv('MYSQLPORT') or os.getenv('MYSQL_PORT') or os.getenv('DB_PORT', '3306')),
            'user': os.getenv('MYSQLUSER') or os.getenv('MYSQL_USER') or os.getenv('DB_USER', 'rtconnect'),
            'password': os.getenv('MYSQLPASSWORD') or os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('MYSQLDATABASE') or os.getenv('MYSQL_DB') or os.getenv('DB_NAME', 'rtconnect_db'),
        }

    ca_path = os.getenv('MIGRATION_MYSQL_SSL_CA') if migration else None
    ca_path = ca_path or os.getenv('MYSQL_SSL_CA')
    ssl_mode = os.getenv('MYSQL_SSL_MODE', 'preferred').lower()
    if ssl_mode not in {'disabled', 'preferred', 'required'}:
        raise RuntimeError('MYSQL_SSL_MODE must be disabled, preferred, or required.')
    if ca_path:
        options.update(ssl_ca=ca_path, ssl_verify_cert=True, ssl_verify_identity=True)
    elif ssl_mode == 'required':
        options['ssl_disabled'] = False
    elif ssl_mode == 'disabled':
        options['ssl_disabled'] = True

    return options


def get_connection(migration=False):
    return pymysql.connect(
        **_connection_options(migration=migration),
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
        local_infile=False,
    )


def query_all(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def query_one(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.lastrowid
    finally:
        conn.close()
