"""Nomor surat resmi yang unik dan berurutan per tahun.

Nomor urut diambil dengan satu statement atomik (INSERT ... ON CONFLICT DO UPDATE ...
RETURNING) pada tabel ``nomor_surat_counter``. Baris terkunci selama transaksi, sehingga
dua pengesahan yang terjadi bersamaan tidak pernah mendapat nomor yang sama.
"""

import datetime

from config import Config
from database.db import transaction

ROMAN_MONTHS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']


def format_letter_number(jenis_kode: str, sequence: int, when: datetime.datetime) -> str:
    month_roman = ROMAN_MONTHS[when.month - 1]
    return (
        f"{Config.RT_NUMBER}/{Config.RW_NUMBER}/{Config.RT_LETTER_CODE}/{jenis_kode}/"
        f"{sequence:03d}/{month_roman}/{when.year}"
    )


def next_letter_sequence(year: int) -> int:
    """Ambil nomor urut berikutnya untuk ``year`` secara atomik (reset tiap tahun)."""
    with transaction() as cur:
        cur.execute(
            """INSERT INTO nomor_surat_counter (tahun, last_number) VALUES (%s, 1)
               ON CONFLICT (tahun) DO UPDATE
                 SET last_number = nomor_surat_counter.last_number + 1
               RETURNING last_number""",
            (year,),
        )
        return cur.fetchone()['last_number']


def generate_unique_letter_number(jenis_kode: str) -> str:
    now = datetime.datetime.now()
    return format_letter_number(jenis_kode, next_letter_sequence(now.year), now)