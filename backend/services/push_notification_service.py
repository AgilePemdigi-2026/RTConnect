"""Layanan Push Notification berbasis Firebase Cloud Messaging (FCM).

Modul ini menginisialisasi Firebase Admin SDK secara aman dan menyediakan fungsi
untuk mengirim push notification ke perangkat pengguna (Android/iOS) baik dalam kondisi
foreground, background, maupun terminated.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

_app_initialized = False
_FCM_CHANNEL_ID = "rtconnect_high_importance_channel"


def _resolve_credentials_path() -> Optional[Path]:
    """Mencari lokasi berkas firebase-service-account.json."""
    env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    base_dir = Path(__file__).resolve().parent.parent
    candidates = [
        base_dir / "firebase-service-account.json",
        base_dir.parent / "firebase-service-account.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Cari berkas dengan pola *firebase-adminsdk*.json jika ada
    for match in base_dir.glob("*firebase-adminsdk*.json"):
        return match

    return None


def init_firebase_admin() -> bool:
    """Inisialisasi Firebase Admin SDK (idempotent / singleton)."""
    global _app_initialized
    if _app_initialized:
        return True

    if firebase_admin._apps:
        _app_initialized = True
        return True

    cred_path = _resolve_credentials_path()
    if not cred_path:
        logger.warning(
            "[FCM] Kredensial Firebase service account tidak ditemukan. "
            "Push notification dinonaktifkan sampai berkas 'firebase-service-account.json' disediakan."
        )
        return False

    try:
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
        _app_initialized = True
        logger.info(f"[FCM] Firebase Admin SDK berhasil diinisialisasi menggunakan {cred_path.name}")
        return True
    except Exception as e:
        logger.error(f"[FCM] Gagal inisialisasi Firebase Admin SDK: {e}", exc_info=True)
        return False


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> bool:
    """Kirim notifikasi push ke satu FCM token perangkat.
    
    Menyertakan konfigurasi Android channel dengan priority 'high' agar
    sistem operasi memunculkan pop-up / heads-up notification di status bar.
    """
    if not token or not token.strip():
        return False

    if not init_firebase_admin():
        logger.warning(f"[FCM] Gagal kirim notif '{title}': Firebase SDK belum aktif.")
        return False

    string_data = {str(k): str(v) for k, v in (data or {}).items()}

    android_config = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id=_FCM_CHANNEL_ID,
            title=title,
            body=body,
            sound="default",
            default_sound=True,
            priority="high",
            click_action="FLUTTER_NOTIFICATION_CLICK",
        ),
    )

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=string_data,
        token=token.strip(),
        android=android_config,
    )

    try:
        response = messaging.send(message)
        logger.info(f"[FCM] Berhasil kirim pesan '{title}' ke token {token[:12]}... (Message ID: {response})")
        return True
    except messaging.UnregisteredError:
        logger.warning(f"[FCM] Token {token[:12]}... sudah tidak valid/kedaluwarsa (Unregistered).")
        return False
    except FirebaseError as fe:
        logger.error(f"[FCM] Kesalahan Firebase saat mengirim pesan: {fe}")
        return False
    except Exception as exc:
        logger.error(f"[FCM] Terjadi kesalahan tak terduga saat kirim notifikasi: {exc}", exc_info=True)
        return False


def send_multicast_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> int:
    """Kirim notifikasi ke beberapa token sekaligus (misal broadcast ke seluruh pengurus RT)."""
    valid_tokens = [t.strip() for t in tokens if t and t.strip()]
    if not valid_tokens:
        return 0

    if not init_firebase_admin():
        logger.warning(f"[FCM] Gagal multicast '{title}': Firebase SDK belum aktif.")
        return 0

    string_data = {str(k): str(v) for k, v in (data or {}).items()}

    android_config = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id=_FCM_CHANNEL_ID,
            title=title,
            body=body,
            sound="default",
            default_sound=True,
            priority="high",
            click_action="FLUTTER_NOTIFICATION_CLICK",
        ),
    )

    multicast_message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=string_data,
        tokens=valid_tokens,
        android=android_config,
    )

    try:
        batch_response = messaging.send_each_for_multicast(multicast_message)
        logger.info(
            f"[FCM] Multicast selesai: {batch_response.success_count} berhasil, "
            f"{batch_response.failure_count} gagal."
        )
        return batch_response.success_count
    except Exception as exc:
        logger.error(f"[FCM] Kesalahan multicast: {exc}", exc_info=True)
        return 0
