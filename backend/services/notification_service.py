"""Pembuatan notifikasi ke tabel `notifikasi` (penerima: warga atau rt)
dan pengiriman push notification instan ke perangkat HP penerima via Firebase (FCM).
"""

import logging
from database.db import execute
from services.push_notification_service import send_push_notification, send_multicast_notification
from services.user_service import get_user_fcm_token, get_all_rt_fcm_tokens

logger = logging.getLogger(__name__)

_INSERT = """
    INSERT INTO notifikasi
        (penerima_tipe, warga_id, rt_id, pengajuan_id, chat_session_id,
         tipe_notifikasi, judul, isi_notifikasi, tautan_tujuan)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def _dispatch_push_notification(recipient_type, recipient_id, tipe, judul, pesan, tautan=None,
                               pengajuan_id=None, chat_session_id=None):
    """Kirim push notification di latar belakang tanpa mengganggu transaksi basis data."""
    try:
        data_payload = {
            'tipe': str(tipe or 'notifikasi'),
            'judul': str(judul or 'Notifikasi'),
            'pesan': str(pesan or ''),
            'tautan': str(tautan or ''),
            'pengajuan_id': str(pengajuan_id or ''),
            'chat_session_id': str(chat_session_id or ''),
            'click_action': 'FLUTTER_NOTIFICATION_CLICK',
        }

        if recipient_type == 'warga' and recipient_id:
            token = get_user_fcm_token('warga', recipient_id)
            if token:
                send_push_notification(token, judul, pesan, data=data_payload)
            else:
                logger.info(f"[FCM] Warga ID {recipient_id} belum mendaftarkan token perangkat.")

        elif recipient_type == 'rt':
            # Jika recipient_id spesifik diberikan, coba kirim ke RT tersebut
            token = get_user_fcm_token('rt', recipient_id) if recipient_id else None
            if token:
                send_push_notification(token, judul, pesan, data=data_payload)
            else:
                # Bila tidak ada token untuk RT spesifik, broadcast ke seluruh pengurus RT aktif
                all_tokens = get_all_rt_fcm_tokens()
                if all_tokens:
                    send_multicast_notification(all_tokens, judul, pesan, data=data_payload)
                else:
                    logger.info("[FCM] Belum ada pengurus RT yang mendaftarkan token perangkat.")
    except Exception as exc:
        logger.warning(f"[FCM] Gagal mengirim push notification: {exc}")


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

    # Kirim Push Notification ke HP pengguna
    _dispatch_push_notification(
        recipient_type, recipient_id, tipe, judul, pesan,
        tautan=tautan, pengajuan_id=pengajuan_id, chat_session_id=chat_session_id
    )
