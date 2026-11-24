"""Akses data pengguna. Di Supabase pengguna terpisah menjadi tabel `warga` dan `rt`.

Hasil query memakai nama kunci yang sama seperti aplikasi lama (user_id, nama_lengkap,
nomor_telepon, role, tanda_tangan_url, ...) supaya aplikasi Flutter tidak perlu diubah.
"""

from config import Config
from database.db import query_one, query_all

_WARGA_SELECT = """
    SELECT warga_id AS user_id, nik, nama AS nama_lengkap, email, password_hash,
           no_telp AS nomor_telepon, alamat, nomor_rt, nomor_rw,
           'warga'::text AS role, tanda_tangan_digital AS tanda_tangan_url, foto_profil, is_active,
           fcm_token
    FROM warga
"""

_RT_SELECT = """
    SELECT rt_id AS user_id, nik, nama AS nama_lengkap, email, password_hash,
           no_telp AS nomor_telepon, NULL::text AS alamat, nomor_rt, nomor_rw,
           'rt'::text AS role, tanda_tangan_digital AS tanda_tangan_url, foto_profil, is_active,
           fcm_token
    FROM rt
"""

_SELECTS = {'warga': (_WARGA_SELECT, 'warga_id'), 'rt': (_RT_SELECT, 'rt_id')}


def _finish(user):
    if user and not user.get('alamat'):
        user['alamat'] = Config.RT_AREA
    return user


def find_by_identity(identity: str):
    """Cari akun (warga dulu, lalu RT) berdasarkan email atau NIK."""
    for sql, _ in (_SELECTS['warga'], _SELECTS['rt']):
        user = query_one(sql + " WHERE lower(email) = lower(%s) OR nik = %s", (identity, identity))
        if user:
            return _finish(user)
    return None


def get_user(role: str, user_id: int):
    """Ambil akun berdasarkan role (dari token) dan id."""
    if role not in _SELECTS:
        return None
    sql, id_column = _SELECTS[role]
    return _finish(query_one(f"{sql} WHERE {id_column} = %s", (user_id,)))


def nik_or_email_taken(nik: str, email: str):
    """Kembalikan 'NIK' / 'Email' bila sudah terpakai di tabel warga atau rt, selain itu None."""
    for table in ('warga', 'rt'):
        row = query_one(f"SELECT nik, email FROM {table} WHERE nik = %s OR lower(email) = lower(%s)", (nik, email))
        if row:
            return 'NIK' if row['nik'] == nik else 'Email'
    return None


_FIRST_RT_ID_CACHE = None


def first_rt_id():
    global _FIRST_RT_ID_CACHE
    if _FIRST_RT_ID_CACHE is None:
        row = query_one("SELECT rt_id FROM rt WHERE is_active ORDER BY rt_id LIMIT 1")
        _FIRST_RT_ID_CACHE = row['rt_id'] if row else None
    return _FIRST_RT_ID_CACHE


def update_user_profile(role: str, user_id: int, nama: str, no_telp: str, alamat: str = None, email: str = None):
    """Perbarui data profil pengguna."""
    if role not in _SELECTS:
        return None
    if role == 'warga':
        query_one(
            "UPDATE warga SET nama = %s, no_telp = %s, alamat = %s, email = COALESCE(%s, email) WHERE warga_id = %s RETURNING warga_id",
            (nama, no_telp, alamat, email, user_id)
        )
    else:
        query_one(
            "UPDATE rt SET nama = %s, no_telp = %s, email = COALESCE(%s, email) WHERE rt_id = %s RETURNING rt_id",
            (nama, no_telp, email, user_id)
        )
    return get_user(role, user_id)


def update_user_signature(role: str, user_id: int, signature_url: str):
    """Perbarui tanda tangan digital pengguna."""
    if role not in _SELECTS:
        return None
    table = 'rt' if role == 'rt' else 'warga'
    id_column = 'rt_id' if role == 'rt' else 'warga_id'
    query_one(
        f"UPDATE {table} SET tanda_tangan_digital = %s WHERE {id_column} = %s RETURNING {id_column}",
        (signature_url, user_id)
    )
    return get_user(role, user_id)

def update_user_avatar(role: str, user_id: int, foto_profil_key: str):
    """Perbarui foto profil pengguna."""
    if role not in _SELECTS:
        return None
    table = 'rt' if role == 'rt' else 'warga'
    id_column = 'rt_id' if role == 'rt' else 'warga_id'
    query_one(
        f"UPDATE {table} SET foto_profil = %s WHERE {id_column} = %s RETURNING {id_column}",
        (foto_profil_key, user_id)
    )
    return get_user(role, user_id)


def update_user_fcm_token(role: str, user_id: int, fcm_token: str = None):
    """Simpan atau perbarui FCM token perangkat pengguna."""
    if role not in _SELECTS:
        return False
    table = 'rt' if role == 'rt' else 'warga'
    id_column = 'rt_id' if role == 'rt' else 'warga_id'
    query_one(
        f"""UPDATE {table} 
            SET fcm_token = %s, fcm_updated_at = CURRENT_TIMESTAMP 
            WHERE {id_column} = %s 
            RETURNING {id_column}""",
        (fcm_token, user_id)
    )
    return True


def get_user_fcm_token(role: str, user_id: int):
    """Ambil FCM token milik pengguna tertentu."""
    if role not in _SELECTS:
        return None
    table = 'rt' if role == 'rt' else 'warga'
    id_column = 'rt_id' if role == 'rt' else 'warga_id'
    row = query_one(f"SELECT fcm_token FROM {table} WHERE {id_column} = %s", (user_id,))
    return row.get('fcm_token') if row else None


def get_all_rt_fcm_tokens():
    """Ambil seluruh FCM token milik pengurus RT yang aktif."""
    rows = query_all(
        "SELECT fcm_token FROM rt WHERE is_active = TRUE AND fcm_token IS NOT NULL AND fcm_token <> ''"
    )
    return [r['fcm_token'] for r in rows if r.get('fcm_token')]


