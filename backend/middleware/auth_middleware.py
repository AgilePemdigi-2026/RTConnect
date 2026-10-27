import datetime
from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from database.db import query_one

def generate_token(user_id: int, role: str, email: str) -> str:
    """Generate a JWT with the configured expiration period."""
    payload = {
        'sub': str(user_id),
        'role': role,
        'email': email,
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=Config.JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

def jwt_required(f):
    """Decorator untuk memverifikasi JWT Bearer Token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Token autentikasi tidak ditemukan atau tidak valid',
                'data': None,
                'error': 'UNAUTHORIZED'
            }), 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            user_id = int(payload['sub'])
            user = query_one(
                "SELECT user_id, nik, nama_lengkap, email, nomor_telepon, alamat, nomor_rt, nomor_rw, role, tanda_tangan_url, is_active FROM users WHERE user_id = %s",
                (user_id,)
            )
            if not user or not user['is_active']:
                return jsonify({
                    'success': False,
                    'message': 'Pengguna tidak ditemukan atau dinonaktifkan',
                    'data': None,
                    'error': 'UNAUTHORIZED'
                }), 401

            request.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Sesi login telah kedaluwarsa, silakan login kembali',
                'data': None,
                'error': 'TOKEN_EXPIRED'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Sesi login tidak valid, silakan login kembali',
                'data': None,
                'error': 'INVALID_TOKEN'
            }), 401

        return f(*args, **kwargs)
    return decorated_function

def roles_accepted(*allowed_roles):
    """Decorator untuk membatasi akses endpoint berdasarkan role pengguna ('rt', 'warga', 'admin')"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(request, 'current_user') or not request.current_user:
                return jsonify({
                    'success': False,
                    'message': 'Autentikasi diperlukan',
                    'data': None,
                    'error': 'UNAUTHORIZED'
                }), 401

            user_role = request.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'message': f'Akses ditolak: role {user_role} tidak memiliki wewenang',
                    'data': None,
                    'error': 'FORBIDDEN'
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
