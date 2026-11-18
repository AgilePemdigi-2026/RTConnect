import json
import re
import time
from flask import Blueprint, request, jsonify
from config import Config
from database.db import query_all, query_one, execute, execute_returning, transaction
from middleware.auth_middleware import jwt_required, roles_accepted
from services.notification_service import add_notification
from services.rag_service import search_knowledge_base, invalidate_knowledge_chunks_cache
from services.chatbot_rules import (
    is_sensitive_credential_for_storage,
    konteks_pertanyaan,
    mask_pii,
    rujukan_konteks,
    semua_topik,
)
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
    t_req_start = getattr(request, '_t_req_start', None) or time.perf_counter()
    TOTAL_REQUEST_BUDGET = Config.TANYART_LLM_TIMEOUT  # SRS NFR 5.1 target (default 5.0s)
    DB_PERSISTENCE_RESERVE = 2.4  # Detik dicadangkan untuk commit transaksi Supabase di jaringan WAN (mengeliminasi overshoot)

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

    # 1b. Ambil riwayat pesan warga sesi ini (tersanitasi) untuk konteks
    # pertanyaan lanjutan. Mengambil 5 pesan terbaru warga (ORDER BY DESC LIMIT 5)
    # lalu dibalik ke urutan kronologis agar konteks percakapan multi-turn mutakhir.
    riwayat = []
    if session_id:
        try:
            riwayat_rows = query_all(
                """SELECT isi_pesan FROM chatmessage
                   WHERE chat_session_id = %s AND pengirim = 'warga'
                   ORDER BY tanggal_kirim DESC, message_id DESC LIMIT 5""",
                (session_id,),
            )
            riwayat = [
                row['isi_pesan'] for row in reversed(riwayat_rows or [])
                if row.get('isi_pesan')
                and '[Pesan disembunyikan oleh sistem' not in row['isi_pesan']
            ]
        except Exception:
            riwayat = []
    query_efektif = konteks_pertanyaan(query_text, riwayat)

    # 1. Evaluasi keamanan & privasi pre-persistence dan sebelum panggilan eksternal
    # Periksa baik kueri asli maupun kueri setelah penggabungan konteks
    is_sensitive = (
        is_sensitive_credential_for_storage(query_text)
        or is_sensitive_credential_for_storage(query_efektif)
    )

    if is_sensitive:
        # Jangan simpan kredensial rahasia plaintext ke database; gunakan placeholder generik yang aman
        pesan_disimpan = "[Pesan disembunyikan oleh sistem karena memuat data rahasia/kredensial]"
    else:
        # Masking PII (NIK 16 digit & Nomor Telepon dengan pemisah) agar tidak tersimpan mentah dalam chat history
        pesan_disimpan = mask_pii(query_text)

    # 1c. Maksud belum jelas: rujukan tanpa riwayat bertopik -> satu klarifikasi
    if (
        not is_sensitive
        and not semua_topik(query_text)
        and rujukan_konteks(query_text)
        and not semua_topik(query_efektif)
    ):
        execute(
            "INSERT INTO chatmessage (chat_session_id, pengirim, isi_pesan) VALUES (%s, 'warga', %s)",
            (session_id, pesan_disimpan)
        )
        return jsonify({
            'success': True,
            'message': 'Perlu klarifikasi',
            'data': {
                'session_id': session_id,
                'is_escalated': True,
                'answer': ('Maaf, saya belum paham maksud Anda. '
                           'Topik administrasi apa yang ingin ditanyakan?'),
                'citation': None,
                'similarity_score': 0.0,
                'status': 'PERTANYAAN_TIDAK_JELAS',
                'source_id': None,
                'base_score': 0.0,
                'escalation_whatsapp_url': None,
            },
            'error': None,
        }), 200

    # 2. Find matching knowledge with semantic or lexical retrieval & Gemini synthesis
    # Pertanyaan disanitasi (PII dimask) sebelum diteruskan ke embedding atau Gemini
    elapsed_so_far = time.perf_counter() - t_req_start
    rem_for_rag = max(0.0, TOTAL_REQUEST_BUDGET - elapsed_so_far - DB_PERSISTENCE_RESERVE)

    sanitized_query_efektif = mask_pii(query_efektif)
    rag_result = search_knowledge_base(
        sanitized_query_efektif,
        conversation_history=riwayat,
        time_budget=rem_for_rag,
        raw_query=mask_pii(query_text),
    )

    # 3. Catat pesan warga, balasan AI, dan retrieval log dalam 1 transaksi atomik (menghemat ~800ms)
    escalated = rag_result['is_escalated']
    rt_id = first_rt_id() if escalated else None
    with transaction() as cur:
        cur.execute(
            """INSERT INTO chatmessage (chat_session_id, pengirim, isi_pesan)
               VALUES (%s, 'warga', %s)""",
            (session_id, pesan_disimpan)
        )
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
            'escalation_whatsapp_url': rag_result['escalation_whatsapp_url'],
            'retrieval_mode': rag_result.get('retrieval_mode'),
            'ai_generated': rag_result.get('ai_generated', False),
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


# ============================================================================
# SRS REQ-7: Pengelolaan Basis Pengetahuan oleh Ketua RT (Upload, Chunk, Embed)
# ============================================================================

def _chunk_text(text: str) -> list[str]:
    """Pecah dokumen menjadi potongan-potongan bermakna (per aturan/paragraf)."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    chunks = []
    current = []
    for line in lines:
        # Jika baris diawali penomoran aturan atau paragraf mandiri
        if re.match(r'^\d+[\.\)]\s*', line) and current:
            chunks.append(' '.join(current))
            current = [line]
        else:
            current.append(line)
            if sum(len(c) for c in current) > 350:
                chunks.append(' '.join(current))
                current = []
    if current:
        chunks.append(' '.join(current))
    return chunks or [text.strip()]


@chatbot_bp.route('/knowledge', methods=['GET'])
@jwt_required
@roles_accepted('rt')
def get_knowledge_documents():
    """Mengambil daftar dokumen basis pengetahuan (Khusus Ketua RT)."""
    docs = query_all("""
        SELECT k.knowledge_id, k.judul, k.kategori, k.sumber, k.uploaded_by,
               k.tanggal_upload, k.updated_at,
               COUNT(c.chunk_id) AS total_chunks
        FROM knowledgebase k
        LEFT JOIN knowledgechunk c ON k.knowledge_id = c.knowledge_id
        GROUP BY k.knowledge_id, k.judul, k.kategori, k.sumber, k.uploaded_by,
                 k.tanggal_upload, k.updated_at
        ORDER BY k.knowledge_id DESC
    """)
    return jsonify({
        'success': True,
        'message': 'Daftar basis pengetahuan berhasil diambil',
        'data': docs or [],
        'error': None,
    }), 200


@chatbot_bp.route('/knowledge', methods=['POST'])
@jwt_required
@roles_accepted('rt')
def upload_knowledge_document():
    """Mengunggah dokumen basis pengetahuan baru, memecahnya menjadi potongan,
    dan menghitung embedding jika embedding service aktif (SRS REQ-7).
    """
    user = request.current_user
    data = request.get_json(silent=True) or {}

    judul = str(data.get('judul') or '').strip()
    kategori = str(data.get('kategori') or 'administrasi').strip()
    isi_dokumen = str(data.get('isi_dokumen') or '').strip()
    sumber = str(data.get('sumber') or 'SOP Resmi RT').strip()

    if not judul or not isi_dokumen:
        return jsonify({
            'success': False,
            'message': 'Judul dan isi dokumen wajib diisi',
            'data': None,
            'error': 'VALIDATION_ERROR',
        }), 400

    raw_chunks = _chunk_text(isi_dokumen)
    from services.semantic_embedding_service import is_embedding_configured, generate_embedding

    try:
        with transaction() as cur:
            cur.execute(
                """INSERT INTO knowledgebase (judul, kategori, isi_dokumen, sumber, uploaded_by)
                   VALUES (%s, %s, %s, %s, %s) RETURNING knowledge_id""",
                (judul, kategori, isi_dokumen, sumber, user.get('user_id')),
            )
            kb_id = cur.fetchone()['knowledge_id']

            total_embedded = 0
            for idx, chunk_text in enumerate(raw_chunks, start=1):
                vec = None
                if is_embedding_configured():
                    try:
                        vec = json.dumps(generate_embedding(chunk_text))
                        total_embedded += 1
                    except Exception:
                        vec = None

                cur.execute(
                    """INSERT INTO knowledgechunk (knowledge_id, urutan_chunk, isi_chunk, kata_kunci, embedding_vector)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (kb_id, idx, chunk_text, judul, vec),
                )

        invalidate_knowledge_chunks_cache()
        return jsonify({
            'success': True,
            'message': 'Dokumen basis pengetahuan berhasil disimpan dan diproses',
            'data': {
                'knowledge_id': kb_id,
                'judul': judul,
                'total_chunks': len(raw_chunks),
                'total_embedded': total_embedded,
                'embedding_enabled': is_embedding_configured(),
            },
            'error': None,
        }), 201
    except Exception as err:
        return jsonify({
            'success': False,
            'message': f'Gagal menyimpan dokumen: {type(err).__name__}',
            'data': None,
            'error': 'DATABASE_ERROR',
        }), 500


@chatbot_bp.route('/knowledge/<int:knowledge_id>', methods=['PUT'])
@jwt_required
@roles_accepted('rt')
def update_knowledge_document(knowledge_id: int):
    """Memperbarui dokumen basis pengetahuan dan melakukan re-chunking (SRS REQ-7)."""
    existing = query_one("SELECT knowledge_id FROM knowledgebase WHERE knowledge_id = %s", (knowledge_id,))
    if not existing:
        return jsonify({
            'success': False,
            'message': 'Dokumen tidak ditemukan',
            'data': None,
            'error': 'NOT_FOUND',
        }), 404

    data = request.get_json(silent=True) or {}
    judul = str(data.get('judul') or '').strip()
    kategori = str(data.get('kategori') or 'administrasi').strip()
    isi_dokumen = str(data.get('isi_dokumen') or '').strip()
    sumber = str(data.get('sumber') or 'SOP Resmi RT').strip()

    if not judul or not isi_dokumen:
        return jsonify({
            'success': False,
            'message': 'Judul dan isi dokumen wajib diisi',
            'data': None,
            'error': 'VALIDATION_ERROR',
        }), 400

    raw_chunks = _chunk_text(isi_dokumen)
    from services.semantic_embedding_service import is_embedding_configured, generate_embedding

    try:
        with transaction() as cur:
            cur.execute(
                """UPDATE knowledgebase
                   SET judul = %s, kategori = %s, isi_dokumen = %s, sumber = %s, updated_at = CURRENT_TIMESTAMP
                   WHERE knowledge_id = %s""",
                (judul, kategori, isi_dokumen, sumber, knowledge_id),
            )
            # Hapus chunk lama dan buat ulang
            cur.execute("DELETE FROM knowledgechunk WHERE knowledge_id = %s", (knowledge_id,))

            total_embedded = 0
            for idx, chunk_text in enumerate(raw_chunks, start=1):
                vec = None
                if is_embedding_configured():
                    try:
                        vec = json.dumps(generate_embedding(chunk_text))
                        total_embedded += 1
                    except Exception:
                        vec = None

                cur.execute(
                    """INSERT INTO knowledgechunk (knowledge_id, urutan_chunk, isi_chunk, kata_kunci, embedding_vector)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (knowledge_id, idx, chunk_text, judul, vec),
                )

        invalidate_knowledge_chunks_cache()
        return jsonify({
            'success': True,
            'message': 'Dokumen basis pengetahuan berhasil diperbarui',
            'data': {
                'knowledge_id': knowledge_id,
                'judul': judul,
                'total_chunks': len(raw_chunks),
                'total_embedded': total_embedded,
            },
            'error': None,
        }), 200
    except Exception as err:
        return jsonify({
            'success': False,
            'message': f'Gagal memperbarui dokumen: {type(err).__name__}',
            'data': None,
            'error': 'DATABASE_ERROR',
        }), 500


@chatbot_bp.route('/knowledge/<int:knowledge_id>', methods=['DELETE'])
@jwt_required
@roles_accepted('rt')
def delete_knowledge_document(knowledge_id: int):
    """Menghapus dokumen basis pengetahuan beserta seluruh potongannya (Khusus Ketua RT)."""
    existing = query_one("SELECT knowledge_id FROM knowledgebase WHERE knowledge_id = %s", (knowledge_id,))
    if not existing:
        return jsonify({
            'success': False,
            'message': 'Dokumen tidak ditemukan',
            'data': None,
            'error': 'NOT_FOUND',
        }), 404

    try:
        with transaction() as cur:
            cur.execute("DELETE FROM knowledgechunk WHERE knowledge_id = %s", (knowledge_id,))
            cur.execute("DELETE FROM knowledgebase WHERE knowledge_id = %s", (knowledge_id,))

        invalidate_knowledge_chunks_cache()
        return jsonify({
            'success': True,
            'message': 'Dokumen basis pengetahuan berhasil dihapus',
            'data': {'knowledge_id': knowledge_id},
            'error': None,
        }), 200
    except Exception as err:
        return jsonify({
            'success': False,
            'message': f'Gagal menghapus dokumen: {type(err).__name__}',
            'data': None,
            'error': 'DATABASE_ERROR',
        }), 500