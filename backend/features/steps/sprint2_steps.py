"""Step definitions Sprint 2 BDD.

Cakupan:
- Ketua RT meninjau & menindaklanjuti pengajuan (setuju / revisi / tolak)
- Pengesahan surat: PIN keamanan, nomor surat unik berurutan, PDF resmi, TTD basah
- Generative document: asisten AI pengisi formulir + biodata tersimpan
- Revisi oleh warga dengan perubahan / pelengkapan biodata

Gemini TIDAK dipanggil sungguhan: jawaban model disimulasikan (patch
services.ai_fill_service._call_gemini) agar pengujian cepat, deterministik,
dan bisa berjalan di CI tanpa API key maupun internet.
"""
import re

from behave import given, then, when

from config import Config
from database.db import query_one
from services import ai_fill_service
from services.pin_guard_service import reset_pin_attempts

BIODATA_DEFAULT = {
    'pekerjaan': 'Karyawan Swasta',
    'jenis_kelamin': 'Laki-laki',
    'tempat_lahir': 'Surabaya',
    'tanggal_lahir': '1995-08-17',
    'agama': 'Islam',
    'status_kawin': 'Belum Kawin',
    'kewarganegaraan': 'WNI',
    'nomor_kk': '3578080101950001',
    'tujuan': 'Kantor Kelurahan Kedurus',
}


# --------------------------------------------------------------------- helper

def _login(context, identity, password):
    res = context.client.post('/api/v1/auth/login', json={'identity': identity, 'password': password})
    assert res.status_code == 200, f'Login gagal untuk {identity}: {res.data}'
    data = res.get_json()['data']
    return {'Authorization': f"Bearer {data['token']}"}, data['user']['user_id']


def _headers(context, role):
    tokens = getattr(context, 'role_headers', {})
    assert role in tokens, f'Peran "{role}" belum login di skenario ini'
    return tokens[role]


def _save(context, response):
    context.last_response = response
    context.last_json = response.get_json(silent=True) or {}


def _jenis_id(kode):
    row = query_one('SELECT jenis_surat_id FROM jenissurat WHERE kode_surat = %s AND is_aktif = TRUE', (kode,))
    assert row, f'Jenis surat {kode} tidak ditemukan / tidak aktif'
    return row['jenis_surat_id']


def _apply(context, kode, metode, keperluan='Persyaratan administrasi pengujian BDD Sprint 2'):
    res = context.client.post('/api/v1/letters/apply', headers=_headers(context, 'warga'), json={
        'jenis_surat_id': _jenis_id(kode),
        'keperluan': keperluan,
        'metode_tanda_tangan': metode,
        **BIODATA_DEFAULT,
    })
    assert res.status_code == 201, f'Gagal membuat pengajuan: {res.data}'
    pid = res.get_json()['data']['pengajuan_id']
    context.created_letter_ids.append(pid)
    return pid


def _table_to_dict(table):
    return {row['field']: row['value'] for row in table}


# --------------------------------------------------------------------- given

@given('the resident "{resident}" and the RT head "{rt}" are logged in with password "{password}"')
def step_login_both(context, resident, rt, password):
    warga_headers, warga_id = _login(context, resident, password)
    rt_headers, rt_id = _login(context, rt, password)
    context.role_headers = {'warga': warga_headers, 'rt': rt_headers}
    context.warga_id = warga_id
    context.rt_id = rt_id
    reset_pin_attempts(rt_id)  # setiap skenario mulai dengan hitungan salah PIN = 0
    context.add_cleanup(reset_pin_attempts, rt_id)


@given('the resident has a new "{kode}" application with "{metode}" signature')
def step_new_application(context, kode, metode):
    context.app_id = _apply(context, kode, metode)


@given('the RT head has requested a revision with note "{note}"')
def step_given_revision(context, note):
    res = context.client.post(f'/api/v1/letters/{context.app_id}/decision',
                              headers=_headers(context, 'rt'), json={'action': 'revise', 'catatan': note})
    assert res.status_code == 200, f'Gagal meminta revisi: {res.data}'


@given('the application has been signed digitally with PIN "{pin}"')
def step_given_signed(context, pin):
    res = context.client.post(f'/api/v1/letters/{context.app_id}/sign-digital',
                              headers=_headers(context, 'rt'), json={'pin': pin})
    assert res.status_code == 200, f'Gagal mengesahkan surat: {res.data}'
    context.signed_numbers = [res.get_json()['data']['nomor_surat_resmi']]


@given('the AI model will answer with')
@given('the AI model will answer with:')
def step_fake_ai(context):
    answer = {key: (None if value == 'null' else value) for key, value in _table_to_dict(context.table).items()}
    context.ai_received = []

    def fake_call(message, letter_types):
        context.ai_received.append(message)
        return dict(answer)

    original_call, original_key = ai_fill_service._call_gemini, Config.GEMINI_API_KEY
    ai_fill_service._call_gemini = fake_call
    Config.GEMINI_API_KEY = Config.GEMINI_API_KEY or 'bdd-dummy-key'

    def restore():
        ai_fill_service._call_gemini = original_call
        Config.GEMINI_API_KEY = original_key
    context.add_cleanup(restore)


@given('the AI model is unavailable')
def step_ai_down(context):
    def failing_call(message, letter_types):
        raise TimeoutError('Gemini tidak menjawab (simulasi BDD)')

    original_call, original_key = ai_fill_service._call_gemini, Config.GEMINI_API_KEY
    ai_fill_service._call_gemini = failing_call
    Config.GEMINI_API_KEY = Config.GEMINI_API_KEY or 'bdd-dummy-key'

    def restore():
        ai_fill_service._call_gemini = original_call
        Config.GEMINI_API_KEY = original_key
    context.add_cleanup(restore)


# --------------------------------------------------------------------- when

@when('the RT head opens the incoming application queue')
def step_queue(context):
    _save(context, context.client.get('/api/v1/letters/incoming-queue', headers=_headers(context, 'rt')))


@when('the RT head sends decision "{action}" with note "{note}"')
def step_decision(context, action, note):
    _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/decision',
                                       headers=_headers(context, 'rt'), json={'action': action, 'catatan': note}))


@when('the RT head sends decision "{action}" without a note')
def step_decision_no_note(context, action):
    _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/decision',
                                       headers=_headers(context, 'rt'), json={'action': action}))


@when('the resident tries to send decision "{action}" on the application')
def step_decision_by_resident(context, action):
    _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/decision',
                                       headers=_headers(context, 'warga'), json={'action': action, 'catatan': 'x'}))


@when('the RT head signs the application with PIN "{pin}"')
def step_sign(context, pin):
    _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/sign-digital',
                                       headers=_headers(context, 'rt'), json={'pin': pin}))


@when('the RT head enters the wrong PIN "{pin}" {times:d} times')
def step_wrong_pin(context, pin, times):
    for _ in range(times):
        _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/sign-digital',
                                           headers=_headers(context, 'rt'), json={'pin': pin}))


@when('the RT head signs a second new "{kode}" application with PIN "{pin}"')
def step_sign_second(context, kode, pin):
    second_id = _apply(context, kode, 'digital')
    res = context.client.post(f'/api/v1/letters/{second_id}/sign-digital',
                              headers=_headers(context, 'rt'), json={'pin': pin})
    _save(context, res)
    assert res.status_code == 200, f'Gagal mengesahkan surat kedua: {res.data}'
    context.signed_numbers.append(context.last_json['data']['nomor_surat_resmi'])


@when('the RT head confirms the physical signature')
def step_confirm_physical(context):
    _save(context, context.client.post(f'/api/v1/letters/{context.app_id}/confirm-physical',
                                       headers=_headers(context, 'rt')))


@when('the resident downloads the letter PDF')
def step_download(context):
    _save(context, context.client.get(f'/api/v1/letters/{context.app_id}/download',
                                      headers=_headers(context, 'warga')))


@when('the resident asks the AI assistant "{pesan}"')
def step_ai_fill(context, pesan):
    _save(context, context.client.post('/api/v1/letters/ai-fill',
                                       headers=_headers(context, 'warga'), json={'pesan': pesan}))


@when('the resident requests the last applicant data')
def step_last_data(context):
    _save(context, context.client.get('/api/v1/letters/my-last-data', headers=_headers(context, 'warga')))


@when('the resident resubmits the application with')
@when('the resident resubmits the application with:')
def step_resubmit(context):
    payload = _table_to_dict(context.table)
    _save(context, context.client.put(f'/api/v1/letters/{context.app_id}/resubmit',
                                      headers=_headers(context, 'warga'), json=payload))


@when('the resident opens the application detail')
def step_open_detail(context):
    _save(context, context.client.get(f'/api/v1/letters/{context.app_id}', headers=_headers(context, 'warga')))


# --------------------------------------------------------------------- then

@then('the application status in the database should be "{status}"')
def step_db_status(context, status):
    row = query_one('SELECT status::text AS status FROM pengajuansurat WHERE pengajuan_id = %s', (context.app_id,))
    assert row and row['status'] == status, f'Status di database: {row}'


@then('the response content type should be "{content_type}"')
def step_content_type(context, content_type):
    actual = context.last_response.content_type
    assert actual.startswith(content_type), f'Content-Type: {actual}'


@then('the downloaded file should be a valid PDF')
def step_valid_pdf(context):
    assert context.last_response.data[:5] == b'%PDF-', 'File yang diunduh bukan PDF'


@then('the two official letter numbers should be different and sequential')
def step_numbers_sequential(context):
    first, second = context.signed_numbers[-2:]
    assert first != second, f'Nomor surat kembar: {first}'
    # Format: RT/RW/KODE_RT/JENIS/URUT/BULAN_ROMAWI/TAHUN -> ambil nomor urut
    n1, n2 = (int(re.search(r'/(\d{3,})/[IVXLC]+/\d{4}$', n).group(1)) for n in (first, second))
    assert n2 == n1 + 1, f'Nomor urut tidak berurutan: {first} -> {second}'


@then('the queue should contain the application')
def step_queue_contains(context):
    ids = [item.get('pengajuan_id') for item in context.last_json.get('data', [])]
    assert context.app_id in ids, f'Pengajuan {context.app_id} tidak ada di antrean: {ids}'


@then('the AI should not have received "{text}"')
def step_ai_not_received(context, text):
    assert context.ai_received, 'Model AI tidak dipanggil'
    for message in context.ai_received:
        assert text not in message, f'Data sensitif "{text}" ikut terkirim ke AI: {message}'


@then('the AI should have been called')
def step_ai_called(context):
    assert getattr(context, 'ai_received', None), 'Model AI tidak dipanggil'


@then('the response field "{field_path}" should be null')
def step_field_null(context, field_path):
    from common_steps import resolve_field
    value = resolve_field(context.last_json, field_path)
    assert value is None, f'Field {field_path} seharusnya null, ternyata: {value}'


@then('the response field "{field_path}" should not contain "{text}"')
def step_field_not_contains(context, field_path, text):
    from common_steps import resolve_field
    value = resolve_field(context.last_json, field_path)
    assert value is None or text not in value, f'Field {field_path} = {value!r} masih memuat "{text}"'
