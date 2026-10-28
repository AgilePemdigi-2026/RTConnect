import json
import os
import sys
import random

# Tambahkan direktori backend ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def run_api_tests():
    from config import Config
    from routes.letter_routes import reset_pin_attempts
    if not Config.RT_SIGNING_PIN_HASH and not Config.IS_PRODUCTION:
        import bcrypt
        Config.RT_SIGNING_PIN_HASH = bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode('utf-8')
    if not Config.RT_WHATSAPP_NUMBER and not Config.IS_PRODUCTION:
        Config.RT_WHATSAPP_NUMBER = '6281234567890'

    app = create_app()
    client = app.test_client()

    print("==================================================")
    print("      MEMULAI SUITE PENGUJIAN LENGKAP RTCONNECT   ")
    print("==================================================")

    # 1. Health Check
    res = client.get('/api/v1/health')
    assert res.status_code == 200, f"Health check gagal: {res.data}"
    data = res.get_json()
    print("[PASS] 1. Health Check: OK -> Status:", data['data']['status'])

    # 2. Register Warga Baru (API-001)
    rand_nik = f"351508{random.randint(1000000000, 9999999999)}"
    rand_email = f"warga_{rand_nik}@gmail.com"
    res_reg = client.post('/api/v1/auth/register', json={
        'nik': rand_nik,
        'nama_lengkap': 'Warga Uji Coba Baru',
        'email': rand_email,
        'password': 'Password123!',
        'nomor_telepon': '081299887766',
        'alamat': 'Griya Taman Asri Blok E-20'
    })
    assert res_reg.status_code == 201, f"Register gagal: {res_reg.data}"
    print(f"[PASS] 2. Registrasi Warga Baru (API-001): OK -> User ID: {res_reg.get_json()['data']['user_id']}")

    # 3. Login Warga (API-002)
    res_warga = client.post('/api/v1/auth/login', json={
        'identity': 'resident@example.test',
        'password': 'LocalTestOnly#2026'
    })
    assert res_warga.status_code == 200, f"Login Warga gagal: {res_warga.data}"
    warga_token = res_warga.get_json()['data']['token']
    warga_headers = {'Authorization': f'Bearer {warga_token}'}
    print("[PASS] 3. Login Warga (API-002): OK -> Token berhasil diperoleh untuk role 'warga'")

    # 4. Login Ketua RT (API-002)
    res_rt = client.post('/api/v1/auth/login', json={
        'identity': 'rt@example.test',
        'password': 'LocalTestOnly#2026'
    })
    assert res_rt.status_code == 200, f"Login RT gagal: {res_rt.data}"
    rt_data = res_rt.get_json()['data']
    rt_token = rt_data['token']
    rt_user_id = rt_data['user']['user_id']
    rt_headers = {'Authorization': f'Bearer {rt_token}'}
    print("[PASS] 4. Login Ketua RT (API-002): OK -> Token berhasil diperoleh untuk role 'rt'")

    # 5. Profile Me (API-003)
    res_me = client.get('/api/v1/auth/me', headers=warga_headers)
    assert res_me.status_code == 200
    print("[PASS] 5. Profil Pengguna (API-003): OK -> Nama:", res_me.get_json()['data']['nama_lengkap'])

    # 6. Daftar Jenis Surat (API-004)
    res_types = client.get('/api/v1/letters/types', headers=warga_headers)
    assert res_types.status_code == 200
    types = res_types.get_json()['data']
    assert len(types) >= 4
    dom_type = next((t for t in types if t['kode_surat'] == 'DOM'), None)
    ktp_type = next((t for t in types if t['kode_surat'] == 'KTP'), None)
    assert dom_type is not None
    print(f"[PASS] 6. Daftar Jenis Surat (API-004): OK -> Ditemukan {len(types)} jenis surat master")

    # 7. Warga Mengajukan Surat Domisili (Draf Template) (API-005)
    res_apply = client.post('/api/v1/letters/apply', headers=warga_headers, json={
        'jenis_surat_id': dom_type['jenis_surat_id'],
        'keperluan': 'Persyaratan pembukaan rekening bank syariah cabang Sidoarjo',
        'metode_tanda_tangan': 'digital'
    })
    assert res_apply.status_code == 201, f"Apply surat gagal: {res_apply.data}"
    apply_data = res_apply.get_json()['data']
    pengajuan_id = apply_data['pengajuan_id']
    nomor_pengajuan = apply_data['nomor_pengajuan']
    assert apply_data['status'] == 'diajukan'
    assert 'draf_ai' in apply_data
    print(f"[PASS] 7. Pengajuan Surat Warga (API-005): OK -> ID #{pengajuan_id} ({nomor_pengajuan}), draf template dibuat")

    # 8. Riwayat Pengajuan Milik Warga (API-006)
    res_my_apps = client.get('/api/v1/letters/my-applications', headers=warga_headers)
    assert res_my_apps.status_code == 200
    assert len(res_my_apps.get_json()['data']) > 0
    print(f"[PASS] 8. Riwayat Surat Warga (API-006): OK -> Total pengajuan: {len(res_my_apps.get_json()['data'])}")

    # 9. RT Cek Antrean Surat Masuk (API-007)
    res_queue = client.get('/api/v1/letters/incoming-queue', headers=rt_headers)
    assert res_queue.status_code == 200
    queue = res_queue.get_json()['data']
    target_in_queue = next((q for q in queue if q['pengajuan_id'] == pengajuan_id), None)
    assert target_in_queue is not None
    print(f"[PASS] 9. Antrean Masuk RT (API-007): OK -> Surat #{pengajuan_id} terdeteksi di antrean RT")

    # 10. Detail Pengajuan Surat (API-008)
    res_detail = client.get(f'/api/v1/letters/{pengajuan_id}', headers=rt_headers)
    assert res_detail.status_code == 200
    print(f"[PASS] 10. Detail Pengajuan (API-008): OK -> Keperluan: '{res_detail.get_json()['data']['keperluan']}'")

    # 11. RT Menyetujui Pengajuan (Decision: Approve) (API-010)
    res_dec = client.post(f'/api/v1/letters/{pengajuan_id}/decision', headers=rt_headers, json={
        'action': 'approve',
        'catatan': 'Data warga valid dan berkas lengkap'
    })
    assert res_dec.status_code == 200
    assert res_dec.get_json()['data']['status'] == 'disetujui'
    print(f"[PASS] 11. Keputusan RT (API-010): OK -> Pengajuan #{pengajuan_id} disetujui")

    # 12. Uji Brute-Force PIN RT & Otorisasi TTD Digital (API-011 / UC-09 / AUD-11)
    # Skenario A: Percobaan 1-4 dengan PIN salah (harus HTTP 401 dan counter berkurang)
    for attempt in range(1, 5):
        res_wrong = client.post(f'/api/v1/letters/{pengajuan_id}/sign-digital', headers=rt_headers, json={
            'pin': f'99999{attempt}'
        })
        assert res_wrong.status_code == 401, f"Percobaan {attempt} salah PIN gagal menghasilkan 401: {res_wrong.data}"
        wrong_json = res_wrong.get_json()
        assert wrong_json['error'] == 'INVALID_PIN'
        assert wrong_json['data']['sisa_percobaan'] == 5 - attempt

    # Skenario B: Percobaan ke-5 dengan PIN salah (harus memicu lockout HTTP 429)
    res_lock = client.post(f'/api/v1/letters/{pengajuan_id}/sign-digital', headers=rt_headers, json={
        'pin': '999995'
    })
    assert res_lock.status_code == 429, f"Percobaan ke-5 gagal memicu 429: {res_lock.data}"
    lock_json = res_lock.get_json()
    assert lock_json['error'] == 'PIN_LOCKED'
    assert lock_json['data']['sisa_percobaan'] == 0
    assert lock_json['data']['sisa_menit'] == 15

    # Skenario C: Percobaan ke-6 saat status akun terkunci (bahkan dengan PIN benar '123456' tetap diblokir 429)
    res_blocked = client.post(f'/api/v1/letters/{pengajuan_id}/sign-digital', headers=rt_headers, json={
        'pin': '123456'
    })
    assert res_blocked.status_code == 429, f"Percobaan ke-6 saat terkunci tidak mengembalikan 429: {res_blocked.data}"
    assert res_blocked.get_json()['error'] == 'PIN_LOCKED'
    print(f"[PASS] 12a. Proteksi Brute-Force PIN RT (AUD-11): OK -> 5x gagal memicu HTTP 429 Lockout 15 menit & blokir percobaan ke-6")

    # Reset lockout untuk melanjutkan pengujian signing resmi dengan PIN benar
    reset_pin_attempts(rt_user_id)

    # Skenario D: Otorisasi digital berhasil dengan PIN valid '123456' setelah reset
    res_sign = client.post(f'/api/v1/letters/{pengajuan_id}/sign-digital', headers=rt_headers, json={
        'pin': '123456'
    })
    assert res_sign.status_code == 200, f"Sign digital gagal: {res_sign.data}"
    sign_data = res_sign.get_json()['data']
    assert sign_data['status'] == 'selesai'
    print(f"[PASS] 12b. Pengesahan TTD Digital (API-011 / UC-09): OK -> Nomor: {sign_data['nomor_surat_resmi']}, Dokumen PDF terbit")

    # Skenario E: Pengesahan digital langsung dari status 'diajukan' (alur satu klik aplikasi Flutter)
    res_direct_apply = client.post('/api/v1/letters/apply', headers=warga_headers, json={
        'jenis_surat_id': dom_type['jenis_surat_id'],
        'keperluan': 'Keperluan mendesak tanda tangan digital langsung',
        'metode_tanda_tangan': 'digital'
    })
    assert res_direct_apply.status_code == 201
    direct_id = res_direct_apply.get_json()['data']['pengajuan_id']

    res_direct_sign = client.post(f'/api/v1/letters/{direct_id}/sign-digital', headers=rt_headers, json={
        'pin': '123456'
    })
    assert res_direct_sign.status_code == 200, f"Sign digital langsung dari diajukan gagal: {res_direct_sign.data}"
    direct_data = res_direct_sign.get_json()['data']
    assert direct_data['status'] == 'selesai'
    print(f"[PASS] 12c. Pengesahan TTD Digital Langsung dari 'diajukan' (Alur Mobile Flutter): OK -> ID #{direct_id} sukses disahkan")

    # 13. Unduh File PDF Resmi (API-013)
    res_dl = client.get(f'/api/v1/letters/{pengajuan_id}/download', headers=warga_headers)
    assert res_dl.status_code == 200
    assert res_dl.content_type == 'application/pdf'
    assert len(res_dl.data) > 1000
    print(f"[PASS] 13. Unduh PDF Resmi (API-013): OK -> Berkas PDF berhasil diunduh ({len(res_dl.data)} bytes)")

    # 14. Pengajuan Surat Tanda Tangan Basah & Konfirmasi Fisik (API-012)
    res_apply_basah = client.post('/api/v1/letters/apply', headers=warga_headers, json={
        'jenis_surat_id': ktp_type['jenis_surat_id'],
        'keperluan': 'Perpanjangan KTP fisik tanda tangan basah di balai RT',
        'metode_tanda_tangan': 'basah'
    })
    assert res_apply_basah.status_code == 201
    basah_id = res_apply_basah.get_json()['data']['pengajuan_id']

    res_phys = client.post(f'/api/v1/letters/{basah_id}/confirm-physical', headers=rt_headers)
    assert res_phys.status_code == 200
    assert res_phys.get_json()['data']['status'] == 'siap_diambil'
    print(f"[PASS] 14. Konfirmasi TTD Basah (API-012): OK -> Pengajuan #{basah_id} status berubah ke 'siap_diambil'")

    # 15. Pengajuan Ulang Revisi Warga (API-009)
    res_apply_rev = client.post('/api/v1/letters/apply', headers=warga_headers, json={
        'jenis_surat_id': dom_type['jenis_surat_id'],
        'keperluan': 'Keperluan awal belum lengkap',
        'metode_tanda_tangan': 'digital'
    })
    rev_id = res_apply_rev.get_json()['data']['pengajuan_id']

    # RT minta revisi
    client.post(f'/api/v1/letters/{rev_id}/decision', headers=rt_headers, json={
        'action': 'revise',
        'catatan': 'Mohon perjelas tujuan surat domisili'
    })

    # Warga resubmit perbaikan
    res_resubmit = client.put(f'/api/v1/letters/{rev_id}/resubmit', headers=warga_headers, json={
        'keperluan': 'Surat keterangan domisili untuk pendaftaran kerja di Sidoarjo'
    })
    assert res_resubmit.status_code == 200
    assert res_resubmit.get_json()['data']['status'] == 'diajukan'
    print(f"[PASS] 15. Resubmit Revisi Warga (API-009): OK -> Pengajuan #{rev_id} berhasil diajukan ulang")

    # 16. Chatbot Tanya RT — pertanyaan yang cocok dengan basis informasi
    res_chat1 = client.post('/api/v1/chatbot/query', headers=warga_headers, json={
        'query': 'Berapa lama masa berlaku surat pengantar RT?'
    })
    assert res_chat1.status_code == 200
    chat1_data = res_chat1.get_json()['data']
    assert chat1_data['is_escalated'] == False
    assert chat1_data['similarity_score'] >= 0.70
    session_id = chat1_data['session_id']
    print(f"[PASS] 16. Pencarian Tanya RT (cocok): OK -> Score: {chat1_data['similarity_score']}, Jawaban: {chat1_data['answer'][:70]}...")

    # 17. Chatbot Tanya RT — pertanyaan yang dieskalasi
    res_chat2 = client.post('/api/v1/chatbot/query', headers=warga_headers, json={
        'session_id': session_id,
        'query': 'Kapan turnamen catur internasional diselenggarakan?'
    })
    assert res_chat2.status_code == 200
    chat2_data = res_chat2.get_json()['data']
    assert chat2_data['is_escalated'] == True
    assert chat2_data['similarity_score'] < 0.70
    assert 'wa.me' in chat2_data['escalation_whatsapp_url']
    print(f"[PASS] 17. Eskalasi Tanya RT: OK -> Score: {chat2_data['similarity_score']}, Link WA: {chat2_data['escalation_whatsapp_url'][:55]}...")

    # 18. Chatbot Sessions & Message History
    res_sessions = client.get('/api/v1/chatbot/sessions', headers=warga_headers)
    assert res_sessions.status_code == 200
    res_msgs = client.get(f'/api/v1/chatbot/sessions/{session_id}/messages', headers=warga_headers)
    assert res_msgs.status_code == 200
    assert len(res_msgs.get_json()['data']) >= 4
    print(f"[PASS] 18. Riwayat Sesi & Pesan Chatbot: OK -> Ditemukan {len(res_msgs.get_json()['data'])} pesan dalam sesi #{session_id}")

    # 19. Notifikasi Feed (API-015)
    res_notif = client.get('/api/v1/notifications', headers=warga_headers)
    assert res_notif.status_code == 200
    notif_data = res_notif.get_json()['data']
    assert len(notif_data['items']) > 0
    first_notif_id = notif_data['items'][0]['notifikasi_id']
    print(f"[PASS] 19. Feed Notifikasi (API-015): OK -> Total {len(notif_data['items'])} notifikasi, {notif_data['unread_count']} belum dibaca")

    # 20. Tandai Notifikasi Dibaca
    res_read = client.put(f'/api/v1/notifications/{first_notif_id}/read', headers=warga_headers)
    assert res_read.status_code == 200
    print(f"[PASS] 20. Tandai Notifikasi Terbaca: OK -> Notifikasi #{first_notif_id} ditandai dibaca")

    # 21. Validasi Integritas Cache Embedding RAG (AUD-10 / ROAD-05)
    from chatbot.chatbot_service import validasi_integritas_cache
    is_valid, reason = validasi_integritas_cache()
    assert is_valid == True, f"Cache RAG tidak valid: {reason}"
    print(f"[PASS] 21. Validasi Cache RAG (AUD-10): OK -> {reason}")

    # 22. Uji Generator PDF Resmi In-Memory (Stateless & S3 Ready) (AUD-09 / ROAD-05)
    from services.pdf_service import generate_official_letter_pdf_bytes
    dummy_pdf = generate_official_letter_pdf_bytes(
        application=apply_data,
        resident=res_detail.get_json()['data'],
        letter_type={'nama_surat': dom_type['nama_surat'], 'kode_surat': dom_type['kode_surat']},
        official_letter_number=sign_data['nomor_surat_resmi'],
        rt_user={'nama_lengkap': 'Test RT User', 'tanda_tangan_url': 'signatures/rt_indra_signature.png'}
    )
    assert isinstance(dummy_pdf, bytes)
    assert dummy_pdf.startswith(b'%PDF-')
    print(f"[PASS] 22. In-Memory PDF Generator (AUD-09): OK -> Berhasil menghasilkan {len(dummy_pdf)} bytes PDF valid")

    print("\n==================================================")
    print("  SELURUH 22 PENGUJIAN SISTEM LENGKAP BERHASIL 100%! ")
    print("==================================================")

if __name__ == '__main__':
    run_api_tests()
