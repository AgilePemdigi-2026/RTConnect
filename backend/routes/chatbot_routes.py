from flask import Blueprint, request, jsonify
from database.db import query_all, query_one, execute
from middleware.auth_middleware import jwt_required, roles_accepted
from services.rag_service import search_knowledge_base

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/v1/chatbot')

@chatbot_bp.route('/query', methods=['POST'])
@jwt_required
@roles_accepted('warga', 'rt', 'admin')
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
        session_id = execute(
            "INSERT INTO chat_sessions (warga_id, status_sesi) VALUES (%s, 'berlangsung')",
            (user['user_id'],)
        )
    else:
        try:
            session_id = int(session_id)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'ID sesi tidak valid', 'data': None, 'error': 'INVALID_SESSION'}), 400
        existing = query_one("SELECT session_id, warga_id FROM chat_sessions WHERE session_id = %s", (session_id,))
        if not existing:
            return jsonify({'success': False, 'message': 'Sesi tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404
        if existing['warga_id'] != user['user_id']:
            return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    # 1. Catat pertanyaan warga ke tabel chat_messages
    execute(
        "INSERT INTO chat_messages (session_id, pengirim, isi_pesan) VALUES (%s, 'warga', %s)",
        (session_id, query_text)
    )

    # 2. Find matching knowledge with lexical retrieval
    rag_result = search_knowledge_base(query_text)

    # 3. Catat balasan sistem AI ke tabel chat_messages
    execute(
        """INSERT INTO chat_messages 
           (session_id, pengirim, isi_pesan, top_chunk_id, similarity_score) 
           VALUES (%s, 'sistem_ai', %s, %s, %s)""",
        (session_id, rag_result['answer'], rag_result['top_chunk_id'], rag_result['similarity_score'])
    )

    # 4. Jika dieskalasi, perbarui status sesi dan buat notifikasi ke RT
    if rag_result['is_escalated']:
        execute("UPDATE chat_sessions SET status_sesi = 'dieskalasi' WHERE session_id = %s", (session_id,))
        rt_user = query_one("SELECT user_id FROM users WHERE role = 'rt' LIMIT 1")
        if rt_user:
            execute(
                """INSERT INTO notifikasi (penerima_id, tipe_notifikasi, judul, pesan_notifikasi, tautan_tujuan)
                   VALUES (%s, 'eskalasi_chat', %s, %s, %s)""",
                (
                    rt_user['user_id'],
                    'Eskalasi Pertanyaan Warga',
                    f"Warga ({user['nama_lengkap']}) menanyakan hal di luar basis data: '{query_text[:50]}...'",
                    f"/chat/{session_id}"
                )
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
            'escalation_whatsapp_url': rag_result['escalation_whatsapp_url']
        },
        'error': None
    }), 200

@chatbot_bp.route('/sessions', methods=['GET'])
@jwt_required
def get_user_sessions():
    """Mengambil riwayat percakapan pengguna"""
    user_id = request.current_user['user_id']
    sessions = query_all(
        """SELECT s.session_id, s.status_sesi, s.started_at,
                  (SELECT isi_pesan FROM chat_messages WHERE session_id = s.session_id ORDER BY waktu_kirim DESC LIMIT 1) as pesan_terakhir
           FROM chat_sessions s
           WHERE s.warga_id = %s
           ORDER BY s.started_at DESC""",
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
    sess = query_one("SELECT warga_id FROM chat_sessions WHERE session_id = %s", (session_id,))
    if not sess:
        return jsonify({'success': False, 'message': 'Sesi tidak ditemukan', 'data': None, 'error': 'NOT_FOUND'}), 404

    if user['role'] == 'warga' and sess['warga_id'] != user['user_id']:
        return jsonify({'success': False, 'message': 'Akses ditolak', 'data': None, 'error': 'FORBIDDEN'}), 403

    messages = query_all(
        "SELECT message_id, pengirim, isi_pesan, top_chunk_id, similarity_score, waktu_kirim FROM chat_messages WHERE session_id = %s ORDER BY waktu_kirim ASC",
        (session_id,)
    )

    return jsonify({
        'success': True,
        'message': 'Pesan chat berhasil diambil',
        'data': messages,
        'error': None
    }), 200
