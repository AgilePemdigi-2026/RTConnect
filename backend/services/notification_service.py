"""Pembuatan notifikasi ke tabel `notifikasi` (penerima: warga atau rt)."""

from database.db import execute

_INSERT = """
    INSERT INTO notifikasi
        (penerima_tipe, warga_id, rt_id, pengajuan_id, chat_session_id,
         tipe_notifikasi, judul, isi_notifikasi, tautan_tujuan)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def add_notification(recipient_type, recipient_id, tipe, judul, pesan, tautan=None,
                     pengajuan_id=None, chat_session_id=None, cur=None):
    """recipient_type: 'warga' atau 'rt'. Pakai `cur` bila ingin ikut dalam transaksi."""
    if recipient_type not in ('warga', 'rt'):
        raise ValueError("recipient_type harus 'warga' atau 'rt'")
    params = (
        recipient_type,
        recipient_id if recipient_type == 'warga' else None,
        recipient_id if recipient_type == 'rt' else None,
        pengajuan_id, chat_session_id, tipe, judul, pesan, tautan,
    )
    if cur is not None:
        cur.execute(_INSERT, params)
    else:
        execute(_INSERT, params)
        