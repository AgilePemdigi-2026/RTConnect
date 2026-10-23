from flask import Blueprint, request, jsonify
from database.db import query_all, query_one, execute
from middleware.auth_middleware import jwt_required

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')

@notification_bp.route('', methods=['GET'])
@jwt_required
def get_notifications():
    """API-015: Mengambil daftar notifikasi pengguna yang aktif"""
    user_id = request.current_user['user_id']
    notifications = query_all(
        """SELECT notifikasi_id, tipe_notifikasi, judul, pesan_notifikasi, tautan_tujuan, is_dibaca, created_at
           FROM notifikasi
           WHERE penerima_id = %s
           ORDER BY created_at DESC""",
        (user_id,)
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
    user_id = request.current_user['user_id']
    data = request.get_json(silent=True) or {}
    is_dibaca = 1 if data.get('is_dibaca', True) else 0
    execute("UPDATE notifikasi SET is_dibaca = %s WHERE notifikasi_id = %s AND penerima_id = %s", (is_dibaca, id, user_id))
    return jsonify({
        'success': True,
        'message': 'Status notifikasi berhasil diperbarui',
        'data': {'notifikasi_id': id, 'is_dibaca': bool(is_dibaca)},
        'error': None
    }), 200

@notification_bp.route('/read-all', methods=['PUT'])
@jwt_required
def mark_all_as_read():
    """Menandai seluruh notifikasi pengguna telah dibaca"""
    user_id = request.current_user['user_id']
    execute("UPDATE notifikasi SET is_dibaca = 1 WHERE penerima_id = %s", (user_id,))
    return jsonify({
        'success': True,
        'message': 'Seluruh notifikasi ditandai telah dibaca',
        'data': None,
        'error': None
    }), 200
