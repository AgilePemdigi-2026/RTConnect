"""Step definitions for Sprint 3 BDD (Issue #16 & Issue #17).

Cakupan Pengujian:
- Issue #16: Pratinjau dan Unduh Berkas Surat Pengantar PDF Resmi
  - Pengunduhan PDF resmi yang telah disahkan secara digital
  - Pratinjau in-app dokumen PDF resmi
  - Penolakan pengunduhan jika pengajuan belum disahkan (404)
  - Pencegahan IDOR / akses silang warga (403 FORBIDDEN)
  - Akses pengunduhan oleh Ketua RT
  - Validasi ID tidak ditemukan (404) dan tanpa token (401)
- Issue #17: Eskalasi Pertanyaan Chatbot ke WhatsApp Ketua RT
  - Deteksi otomatis pertanyaan di luar cakupan administrasi RT
  - Pembuatan tautan eskalasi WhatsApp (wa.me) dengan format pesan baku
  - Pembaruan status sesi obrolan menjadi 'dieskalasi' di basis data
  - Notifikasi sistem 'eskalasi_chat' otomatis untuk Ketua RT
  - Pertanyaan valid dalam cakupan dijawab langsung tanpa eskalasi
  - Riwayat sesi dan pesan obrolan yang dieskalasi
  - Pencegahan akses lintas sesi obrolan antar warga (403 FORBIDDEN)
  - Validasi akses tanpa token (401 UNAUTHORIZED)
"""
from behave import given, when, then

from config import Config
from database.db import query_one, execute
from services import rag_service, tanyart_llm_service

# Simulasi sintesis LLM deterministik untuk pengujian BDD agar tidak bergantung pada Ollama/internet
def _mock_synthesize(query, chunk, *args, **kwargs):
    citation = tanyart_llm_service.build_citation(chunk)
    fallback = tanyart_llm_service.format_fallback_answer(chunk)
    return f"Berdasarkan {citation}: {fallback}", citation, True

rag_service.synthesize_answer_with_gemini = _mock_synthesize
tanyart_llm_service.synthesize_answer = _mock_synthesize


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def _save_response(context, response):
    """Menyimpan respons HTTP terakhir ke context untuk asersi."""
    context.last_response = response
    context.last_json = response.get_json(silent=True) or {}


def _get_jenis_surat_id(kode):
    """Mencari jenis_surat_id berdasarkan kode surat aktif."""
    row = query_one(
        "SELECT jenis_surat_id FROM jenissurat WHERE kode_surat = %s AND is_aktif = TRUE",
        (kode,)
    )
    assert row, f"Jenis surat dengan kode '{kode}' tidak ditemukan atau tidak aktif"
    return row['jenis_surat_id']


def _create_letter_application(context, kode, headers):
    """Membuat pengajuan surat baru dan mendaftarkannya ke cleanup context."""
    res = context.client.post('/api/v1/letters/apply', headers=headers, json={
        'jenis_surat_id': _get_jenis_surat_id(kode),
        'keperluan': 'Keperluan pengujian BDD Sprint 3',
        'metode_tanda_tangan': 'digital',
        'pekerjaan': 'Karyawan Swasta',
        'jenis_kelamin': 'Laki-laki',
        'tempat_lahir': 'Surabaya',
        'tanggal_lahir': '1995-08-17',
        'agama': 'Islam',
        'status_kawin': 'Belum Kawin',
        'kewarganegaraan': 'WNI',
        'nomor_kk': '3578080101950001',
        'tujuan': 'Kantor Kelurahan Kedurus',
    })
    assert res.status_code == 201, f"Gagal membuat pengajuan surat: {res.data}"
    pid = res.get_json()['data']['pengajuan_id']
    if hasattr(context, 'created_letter_ids'):
        context.created_letter_ids.append(pid)
    return pid


def _sign_letter_digitally(context, app_id, pin='123456'):
    """Ketua RT menandatangani surat secara digital menggunakan PIN."""
    rt_headers = context.role_headers['rt']
    res = context.client.post(
        f'/api/v1/letters/{app_id}/sign-digital',
        headers=rt_headers,
        json={'pin': pin}
    )
    assert res.status_code == 200, f"Gagal mengesahkan surat digital: {res.data}"
    return res.get_json()['data']


def _get_or_create_other_resident(context):
    """Memastikan tersedianya akun warga lain untuk pengujian otorisasi IDOR."""
    if hasattr(context, 'other_resident_headers'):
        return context.other_resident_headers, context.other_resident_id

    other = query_one("SELECT warga_id FROM warga WHERE email = 'other_resident@example.test'")
    if not other:
        payload = {
            'nik': '3578010101990088',
            'nama_lengkap': 'Warga Uji Kedua',
            'email': 'other_resident@example.test',
            'password': 'LocalTestOnly#2026',
            'nomor_telepon': '081298765432',
            'alamat': 'Jl. Mawar No. 8 RT 01 RW 01',
        }
        res = context.client.post('/api/v1/auth/register', json=payload)
        assert res.status_code == 201, f"Gagal mendaftarkan warga kedua: {res.data}"
        data = res.get_json()['data']
        context.other_resident_id = data['user_id']
        if hasattr(context, 'created_user_ids'):
            context.created_user_ids.append(data['user_id'])
        res_login = context.client.post('/api/v1/auth/login', json={
            'identity': payload['email'],
            'password': payload['password'],
        })
        assert res_login.status_code == 200, f"Login warga kedua gagal: {res_login.data}"
        token = res_login.get_json()['data']['token']
    else:
        context.other_resident_id = other['warga_id']
        res = context.client.post('/api/v1/auth/login', json={
            'identity': 'other_resident@example.test',
            'password': 'LocalTestOnly#2026',
        })
        assert res.status_code == 200, f"Login warga kedua gagal: {res.data}"
        token = res.get_json()['data']['token']

    context.other_resident_headers = {'Authorization': f"Bearer {token}"}
    return context.other_resident_headers, context.other_resident_id


# ---------------------------------------------------------------------
# Issue #16: Pratinjau dan Unduh Berkas PDF Resmi
# ---------------------------------------------------------------------

@given('an approved and digitally signed "{kode}" letter application exists for the resident')
def step_given_signed_letter(context, kode):
    warga_headers = context.role_headers['warga']
    pid = _create_letter_application(context, kode, warga_headers)
    _sign_letter_digitally(context, pid)
    context.letter_id = pid


@given('an unapproved letter application with status "{status}" exists for the resident')
def step_given_unapproved_letter(context, status):
    warga_headers = context.role_headers['warga']
    pid = _create_letter_application(context, 'DOM', warga_headers)
    context.letter_id = pid


@given('an approved and digitally signed letter application belongs to another resident')
def step_given_other_resident_signed_letter(context):
    other_headers, _ = _get_or_create_other_resident(context)
    pid = _create_letter_application(context, 'DOM', other_headers)
    _sign_letter_digitally(context, pid)
    context.other_letter_id = pid


@when('the resident requests to download the official letter PDF')
def step_when_resident_downloads_pdf(context):
    res = context.client.get(
        f'/api/v1/letters/{context.letter_id}/download',
        headers=context.role_headers['warga']
    )
    _save_response(context, res)


@when('the resident requests to preview the official letter PDF')
def step_when_resident_previews_pdf(context):
    res = context.client.get(
        f'/api/v1/letters/{context.letter_id}/download',
        headers=context.role_headers['warga']
    )
    _save_response(context, res)


@when('the RT head requests to download the official letter PDF')
def step_when_rt_downloads_pdf(context):
    res = context.client.get(
        f'/api/v1/letters/{context.letter_id}/download',
        headers=context.role_headers['rt']
    )
    _save_response(context, res)


@when('the resident attempts to download the other resident\'s letter PDF')
def step_when_resident_downloads_other_pdf(context):
    res = context.client.get(
        f'/api/v1/letters/{context.other_letter_id}/download',
        headers=context.role_headers['warga']
    )
    _save_response(context, res)


@when('the resident requests to download a letter PDF with non-existent ID {letter_id:d}')
def step_when_download_nonexistent_pdf(context, letter_id):
    res = context.client.get(
        f'/api/v1/letters/{letter_id}/download',
        headers=context.role_headers['warga']
    )
    _save_response(context, res)


@when('an unauthenticated user requests to download the official letter PDF')
def step_when_unauthenticated_download_pdf(context):
    res = context.client.get(f'/api/v1/letters/{context.letter_id}/download')
    _save_response(context, res)


@then('the response binary length should be at least {min_length:d} bytes')
def step_assert_binary_length(context, min_length):
    assert len(context.last_response.data) >= min_length, (
        f"Ukuran berkas biner terlalu kecil: {len(context.last_response.data)} < {min_length} bytes"
    )


@then('the response header "{header_name}" should contain "{substring}"')
def step_assert_header_contains(context, header_name, substring):
    header_val = context.last_response.headers.get(header_name, '')
    assert substring in header_val, (
        f"Header '{header_name}' ({header_val}) tidak memuat substring '{substring}'"
    )


# ---------------------------------------------------------------------
# Issue #17: Eskalasi Chatbot ke WhatsApp Ketua RT
# ---------------------------------------------------------------------

@given('the RT WhatsApp contact number is configured to "{phone_number}"')
def step_given_rt_whatsapp_configured(context, phone_number):
    Config.RT_WHATSAPP_NUMBER = phone_number


@when('the resident sends a chatbot query "{query}"')
def step_when_resident_queries_chatbot(context, query):
    payload = {'query': query}
    if hasattr(context, 'active_session_id') and context.active_session_id:
        payload['session_id'] = context.active_session_id

    res = context.client.post(
        '/api/v1/chatbot/query',
        headers=context.role_headers['warga'],
        json=payload
    )
    _save_response(context, res)
    data = context.last_json.get('data') or {}
    sid = data.get('session_id')
    if sid:
        context.active_session_id = sid
        if hasattr(context, 'created_session_ids') and sid not in context.created_session_ids:
            context.created_session_ids.append(sid)


@then('the chat session status in database should become "{status}"')
def step_assert_session_status(context, status):
    assert hasattr(context, 'active_session_id') and context.active_session_id, "Tidak ada sesi aktif di context"
    row = query_one(
        "SELECT status FROM chatsession WHERE chat_session_id = %s",
        (context.active_session_id,)
    )
    assert row, f"Sesi obrolan ID {context.active_session_id} tidak ditemukan di database"
    assert row['status'] == status, (
        f"Status sesi obrolan diharapkan '{status}', didapatkan '{row['status']}'"
    )


@then('the RT head notification inbox should contain an unread "{tipe}" notification')
def step_assert_rt_notification(context, tipe):
    res = context.client.get('/api/v1/notifications', headers=context.role_headers['rt'])
    assert res.status_code == 200, f"Gagal mengambil notifikasi RT: {res.data}"
    items = res.get_json()['data']['items']
    matching = [
        n for n in items
        if n.get('tipe_notifikasi') == tipe and not n.get('is_dibaca')
    ]
    assert len(matching) > 0, (
        f"Tidak ditemukan notifikasi belum dibaca dengan tipe '{tipe}' pada RT: {items}"
    )


@given('the resident has an escalated chat session with query "{query}"')
def step_given_escalated_session(context, query):
    res = context.client.post(
        '/api/v1/chatbot/query',
        headers=context.role_headers['warga'],
        json={'query': query}
    )
    assert res.status_code == 200, f"Gagal mengirim kueri eskalasi: {res.data}"
    data = res.get_json()['data']
    assert data['is_escalated'] is True, f"Kueri tidak dieskalasi: {data}"
    sid = data['session_id']
    context.escalated_session_id = sid
    context.active_session_id = sid
    if hasattr(context, 'created_session_ids') and sid not in context.created_session_ids:
        context.created_session_ids.append(sid)


@when('the resident retrieves the chatbot session history')
def step_when_resident_retrieves_sessions(context):
    res = context.client.get('/api/v1/chatbot/sessions', headers=context.role_headers['warga'])
    _save_response(context, res)


@then('the chatbot session list should include the escalated session')
def step_assert_session_in_list(context):
    sessions = context.last_json.get('data') or []
    session_ids = [s['session_id'] for s in sessions]
    assert context.escalated_session_id in session_ids, (
        f"Sesi dieskalasi ID {context.escalated_session_id} tidak ada dalam daftar sesi: {session_ids}"
    )


@when('the resident retrieves the messages for the escalated session')
def step_when_resident_retrieves_session_messages(context):
    res = context.client.get(
        f'/api/v1/chatbot/sessions/{context.escalated_session_id}/messages',
        headers=context.role_headers['warga']
    )
    _save_response(context, res)


@then('the session messages should include both "{sender1}" and "{sender2}" entries')
def step_assert_senders_in_messages(context, sender1, sender2):
    messages = context.last_json.get('data') or []
    senders = {m.get('pengirim') for m in messages}
    assert sender1 in senders, f"Pengirim '{sender1}' tidak ditemukan dalam riwayat pesan: {senders}"
    assert sender2 in senders, f"Pengirim '{sender2}' tidak ditemukan dalam riwayat pesan: {senders}"


@given('another resident has an active chatbot session')
def step_given_other_resident_session(context):
    other_headers, _ = _get_or_create_other_resident(context)
    res = context.client.post(
        '/api/v1/chatbot/query',
        headers=other_headers,
        json={'query': 'Halo selamat pagi'}
    )
    assert res.status_code == 200, f"Gagal membuat sesi untuk warga lain: {res.data}"
    sid = res.get_json()['data']['session_id']
    context.other_session_id = sid
    if hasattr(context, 'created_session_ids') and sid not in context.created_session_ids:
        context.created_session_ids.append(sid)


@when('the resident attempts to send a query to the other resident\'s chatbot session')
def step_when_resident_accesses_other_session(context):
    res = context.client.post(
        '/api/v1/chatbot/query',
        headers=context.role_headers['warga'],
        json={
            'session_id': context.other_session_id,
            'query': 'Mencoba membajak sesi warga lain'
        }
    )
    _save_response(context, res)


@when('an unauthenticated user sends a chatbot query "{query}"')
def step_when_unauthenticated_query(context, query):
    res = context.client.post('/api/v1/chatbot/query', json={'query': query})
    _save_response(context, res)
