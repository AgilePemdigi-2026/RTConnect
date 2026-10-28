import re
from behave import given, when, then
from database.db import query_all, query_one

@given('an active letter type exists with code "{kode_surat}"')
def step_check_letter_type(context, kode_surat):
    row = query_one("SELECT jenis_surat_id, kode_surat, nama_surat FROM jenis_surat WHERE kode_surat = %s AND is_aktif = 1", (kode_surat,))
    assert row is not None, f"Letter type {kode_surat} not found in database"
    context.active_letter_type = row

@then('the list should contain a letter type with code "{kode_surat}"')
def step_assert_list_contains_type(context, kode_surat):
    items = context.last_json.get('data', [])
    matched = any(item.get('kode_surat') == kode_surat for item in items)
    assert matched, f"Letter code '{kode_surat}' not found in types list: {items}"

@when('I submit a letter application with')
@when('I submit a letter application with:')
def step_submit_letter(context):
    data_map = {row['field']: row['value'] for row in context.table}
    kode_surat = data_map.get('kode_surat')
    
    # Resolve jenis_surat_id
    if getattr(context, 'active_letter_type', None) and context.active_letter_type.get('kode_surat') == kode_surat:
        jenis_id = context.active_letter_type['jenis_surat_id']
    else:
        row = query_one("SELECT jenis_surat_id FROM jenis_surat WHERE kode_surat = %s", (kode_surat,))
        assert row is not None, f"Letter type {kode_surat} not found"
        jenis_id = row['jenis_surat_id']

    payload = {
        'jenis_surat_id': jenis_id,
        'keperluan': data_map.get('keperluan', ''),
        'metode_tanda_tangan': data_map.get('metode_tanda_tangan', 'digital')
    }
    context.last_response = context.client.post('/api/v1/letters/apply', headers=context.auth_headers, json=payload)
    context.last_json = context.last_response.get_json(silent=True) or {}
    if context.last_response.status_code == 201:
        pid = context.last_json.get('data', {}).get('pengajuan_id')
        if pid:
            context.last_pengajuan_id = pid
            context.created_letter_ids.append(pid)

@when('I submit a letter application with non-existent letter type ID {type_id:d}')
def step_submit_invalid_letter_type(context, type_id):
    payload = {
        'jenis_surat_id': type_id,
        'keperluan': 'Percobaan jenis surat invalid',
        'metode_tanda_tangan': 'digital'
    }
    context.last_response = context.client.post('/api/v1/letters/apply', headers=context.auth_headers, json=payload)
    context.last_json = context.last_response.get_json(silent=True) or {}

@then('the response field "{field_path}" should match pattern "{pattern}"')
def step_assert_field_pattern(context, field_path, pattern):
    from common_steps import resolve_field
    val = resolve_field(context.last_json, field_path)
    assert val is not None, f"Field '{field_path}' is None"
    assert re.search(pattern, str(val)), f"Value '{val}' does not match regex '{pattern}'"

@then('a notification for "{notif_title}" should be recorded for the RT Head')
def step_assert_rt_notification(context, notif_title):
    notif = query_one("SELECT notifikasi_id, judul FROM notifikasi WHERE judul = %s ORDER BY created_at DESC LIMIT 1", (notif_title,))
    assert notif is not None, f"Notification with title '{notif_title}' not found in DB"

@given('an existing letter application exists for "{email}"')
def step_ensure_letter_exists(context, email):
    user = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
    assert user is not None
    app = query_one("SELECT pengajuan_id FROM pengajuan_surat WHERE warga_id = %s ORDER BY pengajuan_id DESC LIMIT 1", (user['user_id'],))
    if not app:
        # Create one if none exists
        dom = query_one("SELECT jenis_surat_id FROM jenis_surat WHERE kode_surat = 'DOM'")
        from database.db import execute
        pid = execute("INSERT INTO pengajuan_surat (nomor_pengajuan, warga_id, jenis_surat_id, keperluan, metode_tanda_tangan, status) VALUES ('SRT-2026-00001', %s, %s, 'Uji Riwayat', 'digital', 'diajukan')", (user['user_id'], dom['jenis_surat_id']))
        context.target_application_id = pid
    else:
        context.target_application_id = app['pengajuan_id']

@when('I send an authenticated GET request for the application detail')
def step_get_app_detail(context):
    pid = getattr(context, 'target_application_id', getattr(context, 'last_pengajuan_id', 1))
    context.last_response = context.client.get(f'/api/v1/letters/{pid}', headers=context.auth_headers)
    context.last_json = context.last_response.get_json(silent=True) or {}
