"""Interactively create the first RT account for a deployment."""

import getpass
import re
from pathlib import Path

import bcrypt
from werkzeug.datastructures import FileStorage

from config import Config
from database.db import execute, query_one
from services.file_storage import store_upload


def main():
    name = input('Full name: ').strip()
    nik = input('16-digit NIK: ').strip()
    email = input('Email: ').strip().lower()
    phone = input('Phone number: ').strip()
    address = input('Address: ').strip()
    signature_path = input('Signature image file path (required in production): ').strip()
    password = getpass.getpass('Password (12+ characters): ')
    confirmation = getpass.getpass('Confirm password: ')

    if not all((name, email, phone, address)) or len(nik) != 16 or not nik.isdigit():
        raise SystemExit('Name, email, phone, and address are required; NIK must contain 16 digits.')
    if (len(name) > 100 or len(email) > 100 or len(phone) > 20 or len(address) > 255
            or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise SystemExit('Profile values are too long or the email address is invalid.')
    if len(password) < 12 or len(password.encode('utf-8')) > 72:
        raise SystemExit('Password must be 12 to 72 bytes long.')
    if password != confirmation:
        raise SystemExit('Passwords do not match.')
    if Config.IS_PRODUCTION and not signature_path:
        raise SystemExit('Production RT accounts must have a signature image to issue signed PDFs.')
    if query_one("SELECT user_id FROM users WHERE role = 'rt' LIMIT 1"):
        raise SystemExit('An RT account already exists. Promote or update an account through a controlled admin process.')
    if query_one('SELECT user_id FROM users WHERE nik = %s OR email = %s', (nik, email)):
        raise SystemExit('That NIK or email is already registered.')

    signature_key = None
    if signature_path:
        path = Path(signature_path).expanduser()
        with path.open('rb') as source:
            signature_key = store_upload(
                FileStorage(stream=source, filename=path.name), 'signatures'
            )

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    execute(
        """INSERT INTO users
           (nik, nama_lengkap, email, password_hash, nomor_telepon, alamat, nomor_rt, nomor_rw, role, tanda_tangan_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'rt', %s)""",
        (nik, name, email, password_hash, phone, address, Config.RT_NUMBER, Config.RW_NUMBER, signature_key),
    )
    print(f'Created RT account for {name}.')


if __name__ == '__main__':
    main()
