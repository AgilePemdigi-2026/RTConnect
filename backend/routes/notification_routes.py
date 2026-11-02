from flask import Blueprint, request, jsonify
from database.db import query_all, execute
from middleware.auth_middleware import jwt_required

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


def _recipient():
    """Kolom penerima di tabel notifikasi sesuai role pengguna yang login."""
    user = request.current_user
    column = 'warga_id' if user['role'] == 'warga' else 'rt_id'
    return user['role'] if user['role'] in ('warga', 'rt') else 'rt', column, user['user_id']


@notification_bp.route('', methods=['GET'])
@jwt_required
def get_notifications():
    """API-015: Mengambil daftar notifikasi pengguna yang aktif"""
    tipe, column, user_id = _recipient()
    notifications = query_all(
        f"""SELECT notifikasi_id,
                   COALESCE(tipe_notifikasi, '') AS tipe_notifikasi,
                   COALESCE(judul, 'Notifikasi') AS judul,
                   isi_notifikasi AS pesan_notifikasi,
                   tautan_tujuan,
                   status_baca AS is_dibaca,
                   tanggal_kirim AS created_at
            FROM notifikasi
            WHERE penerima_tipe = %s AND {column} = %s
            ORDER BY tanggal_kirim DESC, notifikasi_id DESC""",
        (tipe, user_id)
    )

    unread_count = sum(1 for n in notifications if not n['is_dibaca'])

    return jsonify({
        'success': True,
        'message': 'Daftar notifikasi berhasil diambil',
        'data': {
            'unread_count': unread_count,
            'items': notifications
        },
        'error': None
    }), 200

@notification_bp.route('/<int:id>/read', methods=['PUT'])
@jwt_required
def mark_as_read(id: int):
    """Menandai satu notifikasi telah dibaca / toggle status baca"""
    tipe, column, user_id = _recipient()
    data = request.get_json(silent=True) or {}
    is_dibaca = bool(data.get('is_dibaca', True))
    execute(
        f"UPDATE notifikasi SET status_baca = %s WHERE notifikasi_id = %s AND penerima_tipe = %s AND {column} = %s",
        (is_dibaca, id, tipe, user_id)
    )
    return jsonify({
        'success': True,
        'message': 'Status notifikasi berhasil diperbarui',
        'data': {'notifikasi_id': id, 'is_dibaca': is_dibaca},
        'error': None
    }), 200

@notification_bp.route('/read-all', methods=['PUT'])
@jwt_required
def mark_all_as_read():
    """Menandai seluruh notifikasi pengguna telah dibaca"""
    tipe, column, user_id = _recipient()
    execute(
        f"UPDATE notifikasi SET status_baca = TRUE WHERE penerima_tipe = %s AND {column} = %s",
        (tipe, user_id)
    )
    return jsonify({
        'success': True,
        'message': 'Seluruh notifikasi ditandai telah dibaca',
        'data': None,
        'error': None
    }), 200