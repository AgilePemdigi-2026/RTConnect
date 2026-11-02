import os
import random
import secrets
import datetime
from io import BytesIO
from pathlib import PurePosixPath
from flask import Blueprint, request, jsonify, send_file
from config import Config
from database.db import query_all, query_one, execute_returning, transaction
from middleware.auth_middleware import jwt_required, roles_accepted
from services.ai_draft_service import generate_letter_draft
from services.file_storage import read_bytes, store_bytes, store_upload
from services.letter_number_service import generate_unique_letter_number
from services.notification_service import add_notification
from services.pdf_service import generate_official_letter_pdf
from services.pin_guard_service import verify_signing_pin
from services.user_service import first_rt_id

letter_bp = Blueprint('letters', __name__, url_prefix='/api/v1/letters')

# Nama kolom Supabase dipetakan (alias) ke nama yang dipakai aplikasi Flutter.
JENIS_COLUMNS = """j.jenis_surat_id, j.kode_surat, j.nama_jenis AS nama_surat,
                   j.template_surat AS template_dokumen, j.persyaratan_dokumen"""

PENGAJUAN_COLUMNS = """p.pengajuan_id, p.nomor_pengajuan, p.warga_id, p.rt_id, p.jenis_surat_id,
       p.tujuan_surat AS keperluan, p.metode_tanda_tangan, p.berkas_lampiran_url,
       (SELECT d.isi_draft FROM draftsurat d WHERE d.pengajuan_id = p.pengajuan_id
         ORDER BY d.versi_ke DESC, d.draft_id DESC LIMIT 1) AS draf_ai_konten,
       p.status, p.catatan_revisi, p.alasan_penolakan, p.tanggal_pengajuan,
       p.tanggal_diverifikasi, p.tanggal_selesai"""

STATUS_PENGESAHAN = """CASE WHEN sf.surat_final_id IS NULL THEN NULL
            WHEN sf.jenis_ttd::text = 'digital' THEN 'digital_sah'
            ELSE 'basah_selesai' END"""


def get_pengajuan(pengajuan_id):
    return query_one(
        f"SELECT {PENGAJUAN_COLUMNS} FROM pengajuansurat p WHERE p.pengajuan_id = %s",
        (pengajuan_id,)
    )


def get_jenis(jenis_surat_id):
    return query_one(
        f"SELECT {JENIS_COLUMNS} FROM jenissurat j WHERE j.jenis_surat_id = %s",
        (jenis_surat_id,)
    )

def generate_nomor_pengajuan() -> str:
    year = datetime.datetime.now().year
    rand_id = random.randint(10000, 99999)
    return f"SRT-{year}-{rand_id}"

def generate_nomor_surat_resmi(jenis_kode: str) -> str:
    # Nomor urut berurutan per tahun (bukan acak) agar selalu unik.
    return generate_unique_letter_number(jenis_kode)

@letter_bp.route('/types', methods=['GET'])
@jwt_required
def get_letter_types():
    """API-004: Mengambil daftar jenis surat yang tersedia"""
    types = query_all(f"SELECT {JENIS_COLUMNS} FROM jenissurat j WHERE j.is_aktif = TRUE ORDER BY j.jenis_surat_id")
    return jsonify({
        'success': True,
        'message': 'Daftar jenis surat berhasil diambil',
        'data': types,
        'error': None
    }), 200

@letter_bp.route('/apply', methods=['POST'])
@jwt_required
@roles_accepted('warga')
def apply_letter():
    """API-005: Warga mengajukan permohonan surat pengantar baru"""
    user = request.current_user
    
    if request.is_json:
        parsed_data = request.get_json(silent=True)
        data = parsed_data if isinstance(parsed_data, dict) else {}
        lampiran_file = None
    else:
        data = request.form.to_dict()
        lampiran_file = request.files.get('lampiran')

    try:
        jenis_surat_id = int(data.get('jenis_surat_id'))
    except (TypeError, ValueError):
        jenis_surat_id = 0
    keperluan_value = data.get('keperluan')
    keperluan = keperluan_value.strip() if isinstance(keperluan_value, str) else ''
    metode_value = data.get('metode_tanda_tangan', 'digital')
    metode_tanda_tangan = metode_value if isinstance(metode_value, str) else ''

    if not jenis_surat_id or not keperluan or len(keperluan) > 2000:
        return jsonify({
            'success': False,
            'message': 'Jenis surat dan keperluan wajib diisi; keperluan maksimal 2000 karakter',
            'data': None,
            'error': 'VALIDATION_ERROR'
        }), 400
    if metode_tanda_tangan not in {'digital', 'basah'}:
        return jsonify({'success': False, 'message': 'Metode tanda tangan tidak valid', 'data': None, 'error': 'VALIDATION_ERROR'}), 400

    jenis = get_jenis(jenis_surat_id)
    if not jenis:
        return jsonify({
            'success': False,
            'message': 'Jenis surat tidak valid atau tidak ditemukan',
            'data': None,
            'error': 'NOT_FOUND'
        }), 404

    # Simpan lampiran dengan nama acak setelah memeriksa ukuran dan isi file.
    lampiran_url = None
    if lampiran_file and lampiran_file.filename:
        try:
            lampiran_url = store_upload(lampiran_file, 'attachments')
        except ValueError as error:
            return jsonify({'success': False, 'message': str(error), 'data': None, 'error': 'INVALID_UPLOAD'}), 400

    # Susun draf deterministik dari template
    draf_ai = generate_letter_draft(user, jenis, keperluan)
    nomor_pengajuan = generate_nomor_pengajuan()

    rt_id = first_rt_id()
    with transaction() as cur:
        cur.execute(
            """INSERT INTO pengajuansurat
               (nomor_pengajuan, warga_id, jenis_surat_id, tujuan_surat, metode_tanda_tangan, berkas_lampiran_url, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'diajukan')
               RETURNING pengajuan_id""",
            (nomor_pengajuan, user['user_id'], jenis_surat_id, keperluan, metode_tanda_tangan, lampiran_url)
        )
        pengajuan_id = cur.fetchone()['pengajuan_id']
        cur.execute(
            "INSERT INTO draftsurat (pengajuan_id, isi_draft, versi_ke, dibuat_oleh_ai) VALUES (%s, %s, 1, TRUE)",
            (pengajuan_id, draf_ai)
        )
        # Tambah Notifikasi untuk Ketua RT
        if rt_id:
            add_notification(
                'rt', rt_id, 'pengajuan_baru', 'Pengajuan Surat Baru',
                f"Pengajuan {jenis['nama_surat']} baru dari {user['nama_lengkap']}",
                f"/letters/{pengajuan_id}", pengajuan_id=pengajuan_id, cur=cur
            )

    return jsonify({
        'success': True,
        'message': 'Pengajuan berhasil dikirim dan draf surat sedang disiapkan',
        'data': {
            'pengajuan_id': pengajuan_id,
            'nomor_pengajuan': nomor_pengajuan,
            'status': 'diajukan',
            'draf_ai': draf_ai,
            'tanggal_pengajuan': datetime.datetime.now().isoformat()
        },
        'error': None
    }), 201

@letter_bp.route('/my-applications', methods=['GET'])
@jwt_required
@roles_accepted('warga')
def get_my_applications():
    """API-006: Mengambil riwayat pengajuan surat milik warga yang login"""
    user_id = request.current_user['user_id']
    applications = query_all(
        """SELECT p.pengajuan_id, p.nomor_pengajuan, p.tujuan_surat AS keperluan, p.metode_tanda_tangan,
                  p.status, p.catatan_revisi, p.alasan_penolakan, p.tanggal_pengajuan, p.tanggal_selesai,
                  j.nama_jenis AS nama_surat, j.kode_surat,
                  sf.nomor_surat_resmi, sf.surat_final_id
           FROM pengajuansurat p
           JOIN jenissurat j ON p.jenis_surat_id = j.jenis_surat_id
           LEFT JOIN suratfinal sf ON p.pengajuan_id = sf.pengajuan_id
           WHERE p.warga_id = %s
           ORDER BY p.tanggal_pengajuan DESC, p.pengajuan_id DESC""",
        (user_id,)
    )

    return jsonify({
        'success': True,
        'message': 'Riwayat pengajuan berhasil diambil',
        'data': applications,
        'error': None
    }), 200

@letter_bp.route('/incoming-queue', methods=['GET'])
@jwt_required
@roles_accepted('rt', 'admin')
def get_incoming_queue():
    """API-007: Mengambil antrean surat masuk untuk verifikasi Ketua RT"""
    queue = query_all(
        """SELECT p.pengajuan_id, p.nomor_pengajuan, p.tujuan_surat AS keperluan, p.metode_tanda_tangan,
                  p.status, p.tanggal_pengajuan, p.catatan_revisi,
                  w.warga_id, w.nama AS nama_lengkap, w.nik, w.alamat, w.no_telp AS nomor_telepon,
                  j.nama_jenis AS nama_surat, j.kode_surat
           FROM pengajuansurat p
           JOIN warga w ON p.warga_id = w.warga_id
           JOIN jenissurat j ON p.jenis_surat_id = j.jenis_surat_id
           ORDER BY
             CASE p.status::text
               WHEN 'diajukan' THEN 1
               WHEN 'perlu_revisi' THEN 2
               WHEN 'disetujui' THEN 3
               ELSE 4
             END,
             p.tanggal_pengajuan DESC, p.pengajuan_id DESC"""
    )

    return jsonify({
        'success': True,
        'message': 'Antrean surat masuk berhasil diambil',
        'data': queue,
        'error': None
    }), 200

@letter_bp.route('/<int:id>', methods=['GET'])
@jwt_required
def get_application_detail(id: int):
    """API-008: Mengambil detail permohonan surat dan draf AI"""
    user = request.current_user

    app_data = query_one(
        f"""SELECT {PENGAJUAN_COLUMNS},
                  w.nama AS nama_lengkap, w.nik, w.alamat, w.no_telp AS nomor_telepon, w.nomor_rt, w.nomor_rw,
                  j.nama_jenis AS nama_surat, j.kode_surat, j.template_surat AS template_dokumen,
                  sf.nomor_surat_resmi, {STATUS_PENGESAHAN} AS status_pengesahan,
                  sf.tanggal_terbit, sf.file_pdf_path
           FROM pengajuansurat p
           JOIN warga w ON p.warga_id = w.warga_id
           JOIN jenissurat j ON p.jenis_surat_id = j.jenis_surat_id
           LEFT JOIN suratfinal sf ON p.pengajuan_id = sf.pengajuan_id
           WHERE p.pengajuan_id = %s""",
        (id,)
    )

    if not app_data:
        return jsonify({
            'success': False,
            'message': 'Pengajuan surat tidak ditemukan',
            'data': None,
            'error': 'NOT_FOUND'
        }), 404

    # Warga hanya dapat melihat pengajuan miliknya sendiri
    if user['role'] == 'warga' and app_data['warga_id'] != user['user_id']:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak: Anda tidak memiliki akses ke pengajuan ini',
            'data': None,
            'error': 'FORBIDDEN'
        }), 403

    return jsonify({
        'success': True,
        'message': 'Detail pengajuan berhasil diambil',
        'data': app_data,
        'error': None
    }), 200

@letter_bp.route('/<int:id>/resubmit', methods=['PUT'])
@jwt_required
@roles_accepted('warga')
def resubmit_application(id: int):
    """API-009: Warga mengajukan ulang revisi dokumen surat"""
    user = request.current_user
    app_data = get_pengajuan(id)

    if not app_data:
        return jsonify({'success': False, 'message': 'Pengajuan tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    if app_data['warga_id'] != user['user_id']:
        return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    if request.is_json:
        parsed_data = request.get_json(silent=True)
        data = parsed_data if isinstance(parsed_data, dict) else {}
    else:
        data = request.form.to_dict()
    keperluan_value = data.get('keperluan', app_data['keperluan'])
    keperluan = keperluan_value.strip() if isinstance(keperluan_value, str) else ''
    if not keperluan or len(keperluan) > 2000:
        return jsonify({'success': False, 'message': 'Keperluan wajib diisi dan maksimal 2000 karakter', 'data': None, 'error': 'VALIDATION_ERROR'}), 400

    jenis = get_jenis(app_data['jenis_surat_id'])
    new_draft = generate_letter_draft(user, jenis, keperluan)

    with transaction() as cur:
        cur.execute(
            """UPDATE pengajuansurat
               SET tujuan_surat = %s, status = 'diajukan', catatan_revisi = NULL
               WHERE pengajuan_id = %s""",
            (keperluan, id)
        )
        cur.execute(
            """INSERT INTO draftsurat (pengajuan_id, isi_draft, versi_ke, dibuat_oleh_ai)
               VALUES (%s, %s,
                       COALESCE((SELECT MAX(versi_ke) FROM draftsurat WHERE pengajuan_id = %s), 0) + 1,
                       TRUE)""",
            (id, new_draft, id)
        )

    return jsonify({
        'success': True,
        'message': 'Pengajuan telah berhasil diperbarui dan diajukan kembali ke RT',
        'data': {'pengajuan_id': id, 'status': 'diajukan', 'draf_ai': new_draft},
        'error': None
    }), 200

@letter_bp.route('/<int:id>/decision', methods=['POST'])
@jwt_required
@roles_accepted('rt', 'admin')
def submit_decision(id: int):
    """API-010: Keputusan evaluasi Ketua RT (approve / revise / reject)"""
    parsed_data = request.get_json(silent=True)
    data = parsed_data if isinstance(parsed_data, dict) else {}
    action = data.get('action') # 'approve', 'revise', 'reject'
    note_value = data.get('catatan') or data.get('alasan') or ''
    catatan = note_value.strip() if isinstance(note_value, str) else ''

    if action not in ['approve', 'revise', 'reject']:
        return jsonify({
            'success': False,
            'message': "Action harus salah satu dari: 'approve', 'revise', atau 'reject'",
            'data': None,
            'error': 'INVALID_ACTION'
        }), 400

    app_data = get_pengajuan(id)
    if not app_data:
        return jsonify({'success': False, 'message': 'Pengajuan surat tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    rt_user = request.current_user

    if action == 'approve':
        status = 'disetujui'
        # Nomor surat resmi diterbitkan saat pengesahan (sign-digital) agar
        # nomor urut tidak terpakai oleh surat yang belum disahkan.
        nomor_resmi = None
        with transaction() as cur:
            cur.execute(
                "UPDATE pengajuansurat SET status = %s, rt_id = %s, tanggal_diverifikasi = LOCALTIMESTAMP WHERE pengajuan_id = %s",
                (status, rt_user['user_id'], id)
            )
            add_notification(
                'warga', app_data['warga_id'], 'surat_disetujui', 'Surat Pengantar Disetujui',
                f"Surat Anda {app_data['nomor_pengajuan']} telah disetujui oleh Ketua RT",
                f"/letters/{id}", pengajuan_id=id, cur=cur
            )
        return jsonify({
            'success': True,
            'message': 'Pengajuan berhasil disetujui',
            'data': {'pengajuan_id': id, 'status': status, 'nomor_surat_resmi': nomor_resmi},
            'error': None
        }), 200

    elif action == 'revise':
        if not catatan:
            return jsonify({'success': False, 'message': 'Catatan perbaikan wajib diisi jika meminta revisi', 'data': None, 'error': 'NOTE_REQUIRED'}), 400
        status = 'perlu_revisi'
        with transaction() as cur:
            cur.execute(
                "UPDATE pengajuansurat SET status = %s, catatan_revisi = %s, rt_id = %s WHERE pengajuan_id = %s",
                (status, catatan, rt_user['user_id'], id)
            )
            add_notification(
                'warga', app_data['warga_id'], 'perlu_revisi', 'Pengajuan Perlu Revisi',
                f"Catatan Pak RT: {catatan}", f"/letters/{id}", pengajuan_id=id, cur=cur
            )
        return jsonify({
            'success': True,
            'message': 'Permintaan revisi berhasil dikirim ke warga',
            'data': {'pengajuan_id': id, 'status': status, 'catatan_revisi': catatan},
            'error': None
        }), 200

    else: # reject
        if not catatan:
            return jsonify({'success': False, 'message': 'Alasan penolakan wajib diisi', 'data': None, 'error': 'REASON_REQUIRED'}), 400
        status = 'ditolak'
        with transaction() as cur:
            cur.execute(
                "UPDATE pengajuansurat SET status = %s, alasan_penolakan = %s, rt_id = %s, tanggal_diverifikasi = LOCALTIMESTAMP WHERE pengajuan_id = %s",
                (status, catatan, rt_user['user_id'], id)
            )
            add_notification(
                'warga', app_data['warga_id'], 'surat_ditolak', 'Pengajuan Surat Ditolak',
                f"Alasan: {catatan}", f"/letters/{id}", pengajuan_id=id, cur=cur
            )
        return jsonify({
            'success': True,
            'message': 'Pengajuan surat telah ditolak',
            'data': {'pengajuan_id': id, 'status': status, 'alasan_penolakan': catatan},
            'error': None
        }), 200

@letter_bp.route('/<int:id>/sign-digital', methods=['POST'])
@jwt_required
@roles_accepted('rt', 'admin')
def sign_digital(id: int):
    """
    API-011: Otorisasi digital PIN Ketua RT & pembuatan dokumen PDF resmi 
    dengan tempelan gambar tanda tangan digital (UC-09).
    """
    parsed_data = request.get_json(silent=True)
    data = parsed_data if isinstance(parsed_data, dict) else {}
    pin_value = data.get('pin', '')
    pin = pin_value.strip() if isinstance(pin_value, str) else ''

    if not Config.RT_SIGNING_PIN_HASH:
        return jsonify({
            'success': False,
            'message': 'Otorisasi tanda tangan belum dikonfigurasi pada server',
            'data': None,
            'error': 'SIGNING_NOT_CONFIGURED'
        }), 503

    if not pin.isdigit() or len(pin) != 6:
        return jsonify({
            'success': False,
            'message': 'PIN harus 6 digit angka',
            'data': None,
            'error': 'VALIDATION_ERROR'
        }), 400

    # Verifikasi PIN + kunci 15 menit setelah 5 kali salah. Status 403/423
    # (bukan 401) agar sesi login Ketua RT tidak ikut dihapus aplikasi.
    pin_check = verify_signing_pin(request.current_user['user_id'], pin)
    if not pin_check.ok:
        return jsonify({
            'success': False,
            'message': pin_check.message,
            'data': pin_check.data(),
            'error': pin_check.error
        }), pin_check.http_status

    app_data = query_one(
        f"""SELECT {PENGAJUAN_COLUMNS}, j.kode_surat, j.nama_jenis AS nama_surat,
                  w.nama AS nama_lengkap, w.nik, w.no_telp AS nomor_telepon, w.alamat, w.nomor_rt, w.nomor_rw
           FROM pengajuansurat p
           JOIN jenissurat j ON p.jenis_surat_id = j.jenis_surat_id
           JOIN warga w ON p.warga_id = w.warga_id
           WHERE p.pengajuan_id = %s""",
        (id,)
    )

    if not app_data:
        return jsonify({'success': False, 'message': 'Pengajuan surat tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404
    if app_data['status'] != 'disetujui':
        return jsonify({'success': False, 'message': 'Pengajuan harus disetujui sebelum ditandatangani', 'data': None, 'error': 'INVALID_STATUS'}), 409

    rt_user = request.current_user
    if Config.IS_PRODUCTION and not rt_user.get('tanda_tangan_url'):
        return jsonify({
            'success': False,
            'message': 'Unggah gambar tanda tangan Ketua RT sebelum menerbitkan surat digital',
            'data': None,
            'error': 'SIGNATURE_NOT_CONFIGURED'
        }), 409
    # Pakai ulang nomor yang sudah pernah terbit untuk pengajuan ini (jika ada)
    existing_number = query_one("SELECT nomor_surat_resmi FROM suratfinal WHERE pengajuan_id = %s", (id,))
    nomor_resmi = (
        existing_number['nomor_surat_resmi']
        if existing_number else generate_nomor_surat_resmi(app_data['kode_surat'])
    )

    # Buat PDF resmi dengan tempelan gambar tanda tangan digital
    pdf_filename = f"Surat_{app_data['nomor_pengajuan']}_{id}.pdf"
    pdf_path = generate_official_letter_pdf(
        application=app_data,
        resident=app_data,
        letter_type={'nama_surat': app_data['nama_surat'], 'kode_surat': app_data['kode_surat']},
        official_letter_number=nomor_resmi,
        rt_user=rt_user,
        output_filename=pdf_filename
    )

    rel_pdf_path = f"generated_letters/{pdf_filename}"
    try:
        with open(pdf_path, 'rb') as generated_pdf:
            store_bytes(rel_pdf_path, generated_pdf.read(), 'application/pdf')
    finally:
        if Config.STORAGE_BACKEND == 's3' and os.path.exists(pdf_path):
            os.remove(pdf_path)
    token_verif = secrets.token_urlsafe(32)

    with transaction() as cur:
        # Simpan atau update ke tabel suratfinal
        cur.execute("SELECT surat_final_id FROM suratfinal WHERE pengajuan_id = %s", (id,))
        existing_sf = cur.fetchone()
        if existing_sf:
            cur.execute(
                """UPDATE suratfinal
                   SET nomor_surat_resmi = %s, file_pdf_path = %s, qr_verification_token = %s,
                       rt_id = %s, jenis_ttd = 'digital', status_konfirmasi_ttd = 'dikonfirmasi',
                       tanggal_ttd = LOCALTIMESTAMP, tanggal_terbit = LOCALTIMESTAMP
                   WHERE pengajuan_id = %s""",
                (nomor_resmi, rel_pdf_path, token_verif, rt_user['user_id'], id)
            )
        else:
            cur.execute(
                """INSERT INTO suratfinal
                   (pengajuan_id, rt_id, nomor_surat_resmi, file_pdf_path, qr_verification_token,
                    jenis_ttd, status_konfirmasi_ttd, tanggal_ttd, tanggal_terbit)
                   VALUES (%s, %s, %s, %s, %s, 'digital', 'dikonfirmasi', LOCALTIMESTAMP, LOCALTIMESTAMP)""",
                (id, rt_user['user_id'], nomor_resmi, rel_pdf_path, token_verif)
            )

        # Perbarui status pengajuan menjadi selesai
        cur.execute(
            "UPDATE pengajuansurat SET status = 'selesai', tanggal_selesai = LOCALTIMESTAMP, rt_id = %s WHERE pengajuan_id = %s",
            (rt_user['user_id'], id)
        )

        # Kirim notifikasi warga
        add_notification(
            'warga', app_data['warga_id'], 'surat_disetujui', 'Surat Selesai Ditandatangani',
            f"Surat {app_data['nama_surat']} Anda telah selesai dan siap diunduh.",
            f"/letters/{id}/download", pengajuan_id=id, cur=cur
        )

    return jsonify({
        'success': True,
        'message': 'PDF diterbitkan dan gambar tanda tangan disematkan',
        'data': {
            'pengajuan_id': id,
            'status': 'selesai',
            'nomor_surat_resmi': nomor_resmi,
            'pdf_url': f"/api/v1/letters/{id}/download",
            'signature_type': 'tempelan_gambar_tanda_tangan_digital'
        },
        'error': None
    }), 200

@letter_bp.route('/<int:id>/confirm-physical', methods=['POST'])
@jwt_required
@roles_accepted('rt', 'admin')
def confirm_physical(id: int):
    """API-012: Otorisasi status tanda tangan basah & siap diambil di kediaman RT"""
    app_data = get_pengajuan(id)
    if not app_data:
        return jsonify({'success': False, 'message': 'Pengajuan tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    rt_user = request.current_user
    with transaction() as cur:
        cur.execute(
            "UPDATE pengajuansurat SET status = 'siap_diambil', rt_id = %s WHERE pengajuan_id = %s",
            (rt_user['user_id'], id)
        )
        # Notifikasi Warga
        add_notification(
            'warga', app_data['warga_id'], 'surat_siap_diambil', 'Surat Siap Diambil',
            "Surat fisik bertanda tangan basah telah selesai dan siap diambil di kediaman Pak RT.",
            f"/letters/{id}", pengajuan_id=id, cur=cur
        )

    return jsonify({
        'success': True,
        'message': 'Status surat fisik berhasil diubah menjadi siap diambil',
        'data': {'pengajuan_id': id, 'status': 'siap_diambil'},
        'error': None
    }), 200

@letter_bp.route('/<int:id>/download', methods=['GET'])
@jwt_required
def download_letter_pdf(id: int):
    """API-013: Mengunduh file PDF resmi yang telah disahkan"""
    user = request.current_user
    app_data = query_one("SELECT pengajuan_id, warga_id FROM pengajuansurat WHERE pengajuan_id = %s", (id,))
    if not app_data:
        return jsonify({'success': False, 'message': 'Pengajuan surat tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    if user['role'] == 'warga' and app_data['warga_id'] != user['user_id']:
        return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    sf = query_one("SELECT file_pdf_path FROM suratfinal WHERE pengajuan_id = %s", (id,))
    if not sf or not sf['file_pdf_path']:
        return jsonify({'success': False, 'message': 'Dokumen PDF surat belum disahkan atau belum tersedia', 'data': None, 'error': 'NOT_FOUND'}), 404

    storage_key = sf['file_pdf_path']
    try:
        pdf_bytes = read_bytes(storage_key)
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'File fisik PDF tidak ditemukan di server', 'data': None, 'error': 'FILE_NOT_FOUND'}), 404

    filename = PurePosixPath(storage_key).name
    return send_file(BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True, download_name=filename)