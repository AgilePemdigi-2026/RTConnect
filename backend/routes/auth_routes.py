import bcrypt
import re
from flask import Blueprint, request, jsonify
from pymysql.err import IntegrityError
from config import Config
from database.db import query_one, execute
from middleware.auth_middleware import generate_token, jwt_required
from services.file_storage import store_upload

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

@auth_bp.route('/register', methods=['POST'])
def register():
    """API-001: Pendaftaran akun warga baru"""
    # Dukung baik multipart/form-data maupun application/json
    if request.is_json:
        parsed_data = request.get_json(silent=True)
        data = parsed_data if isinstance(parsed_data, dict) else {}
        sig_file = None
    else:
        data = request.form.to_dict()
        sig_file = request.files.get('tanda_tangan')

    nik = data.get('nik', '').strip() if isinstance(data.get('nik'), str) else ''
    nama_lengkap = data.get('nama_lengkap', '').strip() if isinstance(data.get('nama_lengkap'), str) else ''
    email = data.get('email', '').strip() if isinstance(data.get('email'), str) else ''
    password = data.get('password', '') if isinstance(data.get('password'), str) else ''
    nomor_telepon = data.get('nomor_telepon', '').strip() if isinstance(data.get('nomor_telepon'), str) else ''
    alamat = data.get('alamat', '').strip() if isinstance(data.get('alamat'), str) else ''

    # Validasi input
    if not (nik and nama_lengkap and email and password and nomor_telepon and alamat):
        return jsonify({
            'success': False,
            'message': 'Semua kolom data (NIK, Nama, Email, Password, No HP, Alamat) wajib diisi',
            'data': None,
            'error': 'VALIDATION_ERROR'
        }), 400

    if len(nik) != 16 or not nik.isdigit():
        return jsonify({
            'success': False,
            'message': 'NIK harus terdiri dari tepat 16 digit angka',
            'data': None,
            'error': 'INVALID_NIK'
        }), 400

    if len(password) < 12 or len(password.encode('utf-8')) > 72:
        return jsonify({
            'success': False,
            'message': 'Password harus 12 sampai 72 byte',
            'data': None,
            'error': 'INVALID_PASSWORD'
        }), 400

    email = email.lower()
    if (len(nama_lengkap) > 100 or len(email) > 100
            or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
            or len(nomor_telepon) > 20 or len(alamat) > 255):
        return jsonify({
            'success': False,
            'message': 'Nama (maks. 100), email valid (maks. 100), telepon (maks. 20), dan alamat (maks. 255) harus diisi dengan benar',
            'data': None,
            'error': 'INVALID_PROFILE'
        }), 400

    # Cek duplikasi NIK atau Email
    existing = query_one("SELECT user_id, nik, email FROM users WHERE nik = %s OR email = %s", (nik, email))
    if existing:
        field = "NIK" if existing['nik'] == nik else "Email"
        return jsonify({
            'success': False,
            'message': f'{field} tersebut sudah terdaftar dalam sistem RTConnect',
            'data': None,
            'error': 'DUPLICATE_ENTRY'
        }), 400

    # Simpan tanda tangan setelah memeriksa format konten dan ukuran file.
    signature_key = None
    if sig_file and sig_file.filename:
        try:
            signature_key = store_upload(sig_file, 'signatures')
        except ValueError as error:
            return jsonify({
                'success': False,
                'message': str(error),
                'data': None,
                'error': 'INVALID_UPLOAD'
            }), 400

    pw_hash = hash_password(password)
    try:
        user_id = execute(
            """INSERT INTO users
               (nik, nama_lengkap, email, password_hash, nomor_telepon, alamat, nomor_rt, nomor_rw, role, tanda_tangan_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'warga', %s)""",
            (nik, nama_lengkap, email, pw_hash, nomor_telepon, alamat, Config.RT_NUMBER, Config.RW_NUMBER, signature_key)
        )
    except IntegrityError:
        return jsonify({
            'success': False,
            'message': 'NIK atau email tersebut sudah terdaftar dalam sistem RTConnect',
            'data': None,
            'error': 'DUPLICATE_ENTRY'
        }), 409

    return jsonify({
        'success': True,
        'message': 'Registrasi berhasil, akun warga telah dibuat',
        'data': {
            'user_id': user_id,
            'nik': nik,
            'nama_lengkap': nama_lengkap,
            'role': 'warga'
        },
        'error': None
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """API-002: Login dengan Email/NIK dan Password"""
    parsed_data = request.get_json(silent=True)
    data = parsed_data if isinstance(parsed_data, dict) else {}
    identity_value = data.get('identity') or data.get('email')
    identity = identity_value.strip() if isinstance(identity_value, str) else ''
    password = data.get('password') if isinstance(data.get('password'), str) else ''

    if not identity or not password:
        return jsonify({
            'success': False,
            'message': 'Email/NIK dan Password wajib diisi',
            'data': None,
            'error': 'MISSING_CREDENTIALS'
        }), 400

    user = query_one(
        "SELECT user_id, nik, nama_lengkap, email, password_hash, nomor_telepon, alamat, nomor_rt, nomor_rw, role, is_active FROM users WHERE email = %s OR nik = %s",
        (identity, identity)
    )

    if not user or not check_password(password, user['password_hash']):
        return jsonify({
            'success': False,
            'message': 'Email/NIK atau password salah',
            'data': None,
            'error': 'UNAUTHORIZED'
        }), 401

    if not user['is_active']:
        return jsonify({
            'success': False,
            'message': 'Akun Anda telah dinonaktifkan oleh administrator',
            'data': None,
            'error': 'ACCOUNT_INACTIVE'
        }), 403

    token = generate_token(user['user_id'], user['role'], user['email'])

    return jsonify({
        'success': True,
        'message': 'Login berhasil',
        'data': {
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'nama_lengkap': user['nama_lengkap'],
                'email': user['email'],
                'nik': user['nik'],
                'nomor_telepon': user['nomor_telepon'],
                'alamat': user['alamat'],
                'nomor_rt': user['nomor_rt'],
                'nomor_rw': user['nomor_rw'],
                'role': user['role']
            }
        },
        'error': None
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user_profile():
    """API-003: Mendapatkan profil pengguna yang sedang login"""
    user = request.current_user
    return jsonify({
        'success': True,
        'message': 'Data profil berhasil diambil',
        'data': {
            'user_id': user['user_id'],
            'nik': user['nik'],
            'nama_lengkap': user['nama_lengkap'],
            'email': user['email'],
            'nomor_telepon': user['nomor_telepon'],
            'alamat': user['alamat'],
            'nomor_rt': user['nomor_rt'],
            'nomor_rw': user['nomor_rw'],
            'role': user['role'],
            'tanda_tangan_digital': user['tanda_tangan_url']
        },
        'error': None
    }), 200
