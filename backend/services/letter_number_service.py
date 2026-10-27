"""Nomor surat resmi yang unik dan berurutan per tahun.

Nomor urut diambil dari tabel ``nomor_surat_counter`` di dalam transaksi
dengan ``SELECT ... FOR UPDATE`` sehingga dua pengesahan yang terjadi
bersamaan tidak pernah mendapat nomor yang sama.
"""

import datetime

from config import Config
from database.db import get_connection

ROMAN_MONTHS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']


def format_letter_number(jenis_kode: str, sequence: int, when: datetime.datetime) -> str:
    month_roman = ROMAN_MONTHS[when.month - 1]
    return (
        f"{Config.RT_NUMBER}/{Config.RW_NUMBER}/{Config.RT_LETTER_CODE}/{jenis_kode}/"
        f"{sequence:03d}/{month_roman}/{when.year}"
    )


def next_letter_sequence(year: int) -> int:
    """Ambil nomor urut berikutnya untuk ``year`` secara atomik (reset tiap tahun)."""
    conn = get_connection()
    try:
        conn.begin()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO nomor_surat_counter (tahun, last_number) VALUES (%s, 0)",
                (year,),
            )
            cursor.execute(
                "SELECT last_number FROM nomor_surat_counter WHERE tahun = %s FOR UPDATE",
                (year,),
            )
            sequence = cursor.fetchone()['last_number'] + 1
            cursor.execute(
                "UPDATE nomor_surat_counter SET last_number = %s WHERE tahun = %s",
                (sequence, year),
            )
        conn.commit()
        return sequence
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def generate_unique_letter_number(jenis_kode: str) -> str:
    now = datetime.datetime.now()
    return format_letter_number(jenis_kode, next_letter_sequence(now.year), now)
