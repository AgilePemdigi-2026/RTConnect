"""Verifikasi PIN pengesahan Ketua RT dengan batas percobaan.

PIN tetap dicocokkan dengan ``RT_SIGNING_PIN_HASH`` (bcrypt). Modul ini
menambahkan penguncian: setelah ``MAX_ATTEMPTS`` kali salah berturut-turut,
PIN untuk akun RT tersebut dikunci selama ``LOCK_MINUTES`` menit.
"""

import bcrypt

from config import Config
from database.db import get_connection

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15


class PinCheckResult:
    def __init__(self, ok, http_status=200, error=None, message='', remaining_attempts=None, locked_minutes=None):
        self.ok = ok
        self.http_status = http_status
        self.error = error
        self.message = message
        self.remaining_attempts = remaining_attempts
        self.locked_minutes = locked_minutes

    def data(self):
        payload = {}
        if self.remaining_attempts is not None:
            payload['sisa_percobaan'] = self.remaining_attempts
        if self.locked_minutes is not None:
            payload['sisa_menit'] = self.locked_minutes
        return payload or None


def _pin_matches(pin: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode('utf-8'), Config.RT_SIGNING_PIN_HASH.encode('utf-8'))
    except ValueError:
        return False


def verify_signing_pin(rt_id: int, pin: str) -> PinCheckResult:
    conn = get_connection()
    try:
        conn.begin()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO rt_pin_attempts (rt_id, gagal_count, locked_until) VALUES (%s, 0, NULL)",
                (rt_id,),
            )
            cursor.execute(
                """SELECT gagal_count,
                          locked_until IS NOT NULL AND locked_until > NOW() AS is_locked,
                          CEIL(TIMESTAMPDIFF(SECOND, NOW(), locked_until) / 60) AS sisa_menit
                   FROM rt_pin_attempts WHERE rt_id = %s FOR UPDATE""",
                (rt_id,),
            )
            row = cursor.fetchone()

            if row['is_locked']:
                conn.commit()
                minutes = max(int(row['sisa_menit'] or 1), 1)
                return PinCheckResult(
                    False, 423, 'PIN_LOCKED',
                    f'PIN terkunci karena salah {MAX_ATTEMPTS} kali. Coba lagi dalam {minutes} menit.',
                    locked_minutes=minutes,
                )

            if _pin_matches(pin):
                cursor.execute(
                    "UPDATE rt_pin_attempts SET gagal_count = 0, locked_until = NULL WHERE rt_id = %s",
                    (rt_id,),
                )
                conn.commit()
                return PinCheckResult(True)

            failed = row['gagal_count'] + 1
            if failed >= MAX_ATTEMPTS:
                cursor.execute(
                    """UPDATE rt_pin_attempts
                       SET gagal_count = 0, locked_until = NOW() + INTERVAL %s MINUTE
                       WHERE rt_id = %s""",
                    (LOCK_MINUTES, rt_id),
                )
                conn.commit()
                return PinCheckResult(
                    False, 423, 'PIN_LOCKED',
                    f'PIN salah {MAX_ATTEMPTS} kali. PIN dikunci selama {LOCK_MINUTES} menit.',
                    locked_minutes=LOCK_MINUTES,
                )

            cursor.execute(
                "UPDATE rt_pin_attempts SET gagal_count = %s, locked_until = NULL WHERE rt_id = %s",
                (failed, rt_id),
            )
            conn.commit()
            remaining = MAX_ATTEMPTS - failed
            return PinCheckResult(
                False, 403, 'INVALID_PIN',
                f'PIN Otorisasi Ketua RT salah. Sisa percobaan: {remaining}',
                remaining_attempts=remaining,
            )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
