import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Muat variabel environment dari .env di backend maupun root folder
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))
load_dotenv()

class Config:
    BASE_DIR = BASE_DIR
    APP_ENV = os.getenv('APP_ENV', 'development').lower()
    IS_PRODUCTION = APP_ENV in {'production', 'prod'}

    # Konfigurasi Database MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST', os.getenv('MYSQLHOST', '127.0.0.1'))
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', os.getenv('MYSQLPORT', '3306')))
    MYSQL_USER = os.getenv('MYSQL_USER', os.getenv('MYSQLUSER', 'rtconnect'))
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', os.getenv('MYSQLPASSWORD', ''))
    MYSQL_DB = os.getenv('MYSQL_DB', os.getenv('MYSQLDATABASE', 'rtconnect_db'))
    MYSQL_SSL_CA = os.getenv('MYSQL_SSL_CA')
    MYSQL_SSL_MODE = os.getenv('MYSQL_SSL_MODE', 'preferred').lower()

    # Keamanan JWT
    # All local workers must share the same key. Production still requires an
    # explicitly configured, randomly generated secret through validate().
    _LOCAL_JWT_SECRET = 'rtconnect-local-development-secret-do-not-use-in-production'
    JWT_SECRET = os.getenv('JWT_SECRET') or (None if IS_PRODUCTION else _LOCAL_JWT_SECRET)
    JWT_EXPIRATION_DAYS = int(os.getenv('JWT_EXPIRATION_DAYS', '1'))
    RT_SIGNING_PIN_HASH = os.getenv('RT_SIGNING_PIN_HASH')

    # Browser clients must opt into CORS. Native mobile apps do not use CORS.
    _default_origins = 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://localhost:8080,http://127.0.0.1:8080'
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', '' if IS_PRODUCTION else _default_origins).split(',')
        if origin.strip()
    ]

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    MAX_UPLOAD_BYTES = 8 * 1024 * 1024
    STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local').lower()
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_REGION = os.getenv('S3_REGION') or os.getenv('AWS_REGION')
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
    S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')

    # Direktori Upload & File
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    SIGNATURES_FOLDER = os.path.join(UPLOAD_FOLDER, 'signatures')
    ATTACHMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'attachments')
    LETTERS_FOLDER = os.path.join(UPLOAD_FOLDER, 'generated_letters')

    # Pengaturan RAG & Chatbot Tanya RT
    RAG_SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.70'))
    RT_WHATSAPP_NUMBER = os.getenv('RT_WHATSAPP_NUMBER', '')
    RT_NAME = os.getenv('RT_NAME', 'Ketua RT')
    RT_NUMBER = os.getenv('RT_NUMBER', '032')
    RW_NUMBER = os.getenv('RW_NUMBER', '08')
    RT_LETTER_CODE = os.getenv('RT_LETTER_CODE', 'GTA')
    RT_AREA = os.getenv('RT_AREA', 'RT 032 / RW 08 Griya Taman Asri')
    RT_LOCATION_LINE_2 = os.getenv('RT_LOCATION_LINE_2', 'PERUMAHAN GRIYA TAMAN ASRI — KELURAHAN SEPANJANG')
    RT_LOCATION_LINE_3 = os.getenv('RT_LOCATION_LINE_3', 'KECAMATAN TAMAN, KABUPATEN SIDOARJO — JAWA TIMUR 61257')
    RT_SIGNING_LOCATION = os.getenv('RT_SIGNING_LOCATION', 'Sidoarjo')

    @classmethod
    def validate(cls):
        if cls.IS_PRODUCTION:
            if (not cls.JWT_SECRET or len(cls.JWT_SECRET) < 32
                    or cls.JWT_SECRET == cls._LOCAL_JWT_SECRET):
                raise RuntimeError('Production requires a unique JWT_SECRET with at least 32 characters.')
            if not cls.RT_SIGNING_PIN_HASH:
                raise RuntimeError('Production requires RT_SIGNING_PIN_HASH.')
            if cls.STORAGE_BACKEND == 'local':
                raise RuntimeError('Production requires private S3-compatible storage.')
            database_url = os.getenv('MYSQL_URL') or os.getenv('DATABASE_URL')
            if database_url and not database_url.startswith(('mysql://', 'mysql+pymysql://')):
                raise RuntimeError('DATABASE_URL must use mysql:// or mysql+pymysql://.')
            if database_url:
                parsed_database_url = urlparse(database_url)
                if not parsed_database_url.hostname or not parsed_database_url.path.strip('/'):
                    raise RuntimeError('DATABASE_URL must include a MySQL host and database name.')
                if not parsed_database_url.password and not any(os.getenv(name) for name in ('MYSQLPASSWORD', 'MYSQL_PASSWORD', 'DB_PASSWORD')):
                    raise RuntimeError('Production requires a non-empty MySQL password.')
            if not database_url and not (os.getenv('MYSQLHOST') or os.getenv('MYSQL_HOST') or os.getenv('DB_HOST')):
                raise RuntimeError('Production requires a MySQL connection URL or host.')
            if not database_url and not (os.getenv('MYSQLPASSWORD') or os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD')):
                raise RuntimeError('Production requires a non-empty MySQL password.')
            if not cls.MYSQL_SSL_CA:
                raise RuntimeError('Production requires MYSQL_SSL_CA so the database certificate and host are verified.')
            if cls.MYSQL_SSL_MODE == 'disabled':
                raise RuntimeError('Production database connections must use TLS.')
            if not cls.CORS_ORIGINS:
                raise RuntimeError('Production requires CORS_ORIGINS for the deployed Flutter web origin.')
            if not cls.RT_WHATSAPP_NUMBER:
                raise RuntimeError('Production requires RT_WHATSAPP_NUMBER in international digits-only format.')
            if not re.fullmatch(r'\d{8,15}', cls.RT_WHATSAPP_NUMBER):
                raise RuntimeError('RT_WHATSAPP_NUMBER must contain 8 to 15 international digits only.')
            if '*' in cls.CORS_ORIGINS:
                raise RuntimeError('Wildcard CORS is not allowed in production.')
            for origin in cls.CORS_ORIGINS:
                parsed_origin = urlparse(origin)
                if (parsed_origin.scheme != 'https' or not parsed_origin.netloc
                        or parsed_origin.path not in {'', '/'}
                        or parsed_origin.query or parsed_origin.fragment
                        or parsed_origin.username or parsed_origin.password):
                    raise RuntimeError('Each production CORS entry must be an exact HTTPS origin, such as https://app.example.com.')
            if not os.path.isfile(cls.MYSQL_SSL_CA):
                raise RuntimeError('MYSQL_SSL_CA must point to a readable CA certificate file.')
            if not cls.RT_SIGNING_PIN_HASH.startswith(('$2a$', '$2b$', '$2y$')):
                raise RuntimeError('RT_SIGNING_PIN_HASH must be a bcrypt hash.')
            if not re.fullmatch(r'\d{1,5}', cls.RT_NUMBER) or not re.fullmatch(r'\d{1,5}', cls.RW_NUMBER):
                raise RuntimeError('RT_NUMBER and RW_NUMBER must contain 1 to 5 digits.')
            if not re.fullmatch(r'[A-Za-z0-9-]{1,10}', cls.RT_LETTER_CODE):
                raise RuntimeError('RT_LETTER_CODE must contain 1 to 10 letters, digits, or hyphens.')
            if bool(cls.S3_ACCESS_KEY_ID) != bool(cls.S3_SECRET_ACCESS_KEY):
                raise RuntimeError('Set both S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY, or use workload identity.')
            if not cls.RT_AREA.strip() or not cls.RT_SIGNING_LOCATION.strip():
                raise RuntimeError('RT_AREA and RT_SIGNING_LOCATION must not be empty.')
        if cls.STORAGE_BACKEND not in {'local', 's3'}:
            raise RuntimeError('STORAGE_BACKEND must be either local or s3.')
        if cls.STORAGE_BACKEND == 's3' and not cls.S3_BUCKET:
            raise RuntimeError('S3_BUCKET is required when STORAGE_BACKEND=s3.')
        if cls.STORAGE_BACKEND == 's3' and cls.IS_PRODUCTION and not cls.S3_REGION:
            raise RuntimeError('S3_REGION or AWS_REGION is required in production.')
        if cls.STORAGE_BACKEND == 's3' and cls.S3_ENDPOINT_URL:
            if urlparse(cls.S3_ENDPOINT_URL).scheme != 'https' and cls.IS_PRODUCTION:
                raise RuntimeError('Production S3_ENDPOINT_URL must use HTTPS.')
        if not 0 <= cls.RAG_SIMILARITY_THRESHOLD <= 1:
            raise RuntimeError('RAG_SIMILARITY_THRESHOLD must be between 0 and 1.')
