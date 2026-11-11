from flask import Blueprint, request, jsonify
from database.db import query_all, query_one, execute, execute_returning, transaction
from middleware.auth_middleware import jwt_required, roles_accepted
from services.notification_service import add_notification
from services.rag_service import search_knowledge_base
from services.chatbot_rules import is_sensitive_credential_for_storage, mask_pii
from services.user_service import first_rt_id

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/v1/chatbot')

@chatbot_bp.route('/query', methods=['POST'])
@jwt_required
@roles_accepted('warga')
def ask_chatbot():
    """
    API-014: Search the Tanya RT knowledge base and escalate low matches.
    Uses the configured lexical-retrieval threshold; low matches are escalated.
    """
    user = request.current_user
    parsed_data = request.get_json(silent=True)
    data = parsed_data if isinstance(parsed_data, dict) else {}
    query_value = data.get('query') or data.get('pertanyaan')
    query_text = query_value.strip() if isinstance(query_value, str) else ''
    session_id = data.get('session_id')

    if not query_text or len(query_text) > 2000:
        return jsonify({
            'success': False,
            'message': 'Pertanyaan wajib diisi dan maksimal 2000 karakter',
            'data': None,
            'error': 'EMPTY_QUERY'
        }), 400

    # Kelola Sesi Obrolan
    if not session_id:
        session_id = execute_returning(
            "INSERT INTO chatsession (warga_id, status) VALUES (%s, 'berlangsung') RETURNING chat_session_id",
            (user['user_id'],)
        )['chat_session_id']
    else:
        try:
            session_id = int(session_id)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'ID sesi tidak valid', 'data': None, 'error': 'INVALID_SESSION'}), 400
        existing = query_one("SELECT chat_session_id AS session_id, warga_id FROM chatsession WHERE chat_session_id = %s", (session_id,))
        if not existing:
            return jsonify({'success': False, 'message': 'Sesi tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404
        if existing['warga_id'] != user['user_id']:
            return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    # 1. Evaluasi keamanan & sanitasi sebelum penyimpanan pesan warga (Privacy P0/P1)
    if is_sensitive_credential_for_storage(query_text):
        # Jangan simpan kredensial rahasia plaintext ke database; gunakan placeholder generik yang aman
        pesan_disimpan = "[Pesan disembunyikan oleh sistem karena memuat data rahasia/kredensial]"
    else:
        # Masking PII (NIK 16 digit & Nomor Telepon dengan pemisah) agar tidak tersimpan mentah dalam chat history
        pesan_disimpan = mask_pii(query_text)

    # 2. Catat pesan warga yang telah disanitasi ke tabel chatmessage
    execute(
        "INSERT INTO chatmessage (chat_session_id, pengirim, isi_pesan) VALUES (%s, 'warga', %s)",
        (session_id, pesan_disimpan)
    )

    # 2. Find matching knowledge with lexical retrieval
    rag_result = search_knowledge_base(query_text)

    # 3. Catat balasan sistem AI ke chatmessage; chunk sumber & skornya ke retrievallog
    escalated = rag_result['is_escalated']
    rt_id = first_rt_id() if escalated else None
    with transaction() as cur:
        cur.execute(
            """INSERT INTO chatmessage (chat_session_id, pengirim, isi_pesan)
               VALUES (%s, 'sistem_ai', %s) RETURNING message_id""",
            (session_id, rag_result['answer'])
        )
        message_id = cur.fetchone()['message_id']
        if rag_result['top_chunk_id'] is not None:
            cur.execute(
                "INSERT INTO retrievallog (message_id, chunk_id, skor_relevansi) VALUES (%s, %s, %s)",
                (message_id, rag_result['top_chunk_id'], rag_result['similarity_score'])
            )

        # 4. Jika dieskalasi, perbarui status sesi dan buat notifikasi ke RT
        if escalated:
            cur.execute("UPDATE chatsession SET status = 'dieskalasi' WHERE chat_session_id = %s", (session_id,))
            if rt_id:
                add_notification(
                    'rt', rt_id, 'eskalasi_chat', 'Eskalasi Pertanyaan Warga',
                    "Warga membutuhkan bantuan administrasi melalui chatbot.",
                    f"/chat/{session_id}", chat_session_id=session_id, cur=cur
                )

    return jsonify({
        'success': True,
        'message': 'Respon berhasil diperoleh',
        'data': {
            'session_id': session_id,
            'is_escalated': rag_result['is_escalated'],
            'answer': rag_result['answer'],
            'citation': rag_result['citation'],
            'similarity_score': rag_result['similarity_score'],
            'status': rag_result.get('status'),
            'source_id': rag_result.get('source_id'),
            'base_score': rag_result.get('base_score'),
            'escalation_whatsapp_url': rag_result['escalation_whatsapp_url']
        },
        'error': None
    }), 200

@chatbot_bp.route('/sessions', methods=['GET'])
@jwt_required
@roles_accepted('warga')
def get_user_sessions():
    """Mengambil riwayat percakapan pengguna"""
    user_id = request.current_user['user_id']
    sessions = query_all(
        """SELECT s.chat_session_id AS session_id, s.status AS status_sesi, s.started_at,
                  (SELECT m.isi_pesan FROM chatmessage m WHERE m.chat_session_id = s.chat_session_id
                   ORDER BY m.tanggal_kirim DESC, m.message_id DESC LIMIT 1) AS pesan_terakhir
           FROM chatsession s
           WHERE s.warga_id = %s
           ORDER BY s.started_at DESC, s.chat_session_id DESC""",
        (user_id,)
    )
    return jsonify({
        'success': True,
        'message': 'Daftar sesi chat berhasil diambil',
        'data': sessions,
        'error': None
    }), 200

@chatbot_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
@jwt_required
def get_session_messages(session_id: int):
    """Mengambil seluruh pesan dalam suatu sesi percakapan"""
    user = request.current_user
    sess = query_one("SELECT warga_id FROM chatsession WHERE chat_session_id = %s", (session_id,))
    if not sess:
        return jsonify({'success': False, 'message': 'Sesi tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    if user['role'] == 'warga' and sess['warga_id'] != user['user_id']:
        return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    messages = query_all(
        """SELECT m.message_id, m.pengirim, m.isi_pesan,
                  r.chunk_id AS top_chunk_id, r.skor_relevansi AS similarity_score,
                  m.tanggal_kirim AS waktu_kirim
           FROM chatmessage m
           LEFT JOIN retrievallog r ON r.message_id = m.message_id
           WHERE m.chat_session_id = %s
           ORDER BY m.tanggal_kirim ASC, m.message_id ASC""",
        (session_id,)
    )

    return jsonify({
        'success': True,
        'message': 'Pesan chat berhasil diambil',
        'data': messages,
        'error': None
    }), 200