"""Cek koneksi asisten AI surat ke server LLM (Ollama kampus / lokal).

Jalankan dari folder backend:
    python cek_llm.py

Di Coolify: buka resource RtConnect -> Terminal, lalu jalankan
    python cek_llm.py

Langkah yang dicek:
1. Konfigurasi .env / Environment Variables (LLM_BASE_URL, LLM_MODEL, timeout)
2. Server LLM bisa dihubungi & daftar model yang terpasang
3. Model LLM_MODEL ada di server
4. Uji ekstraksi formulir surat (cerita contoh -> jenis surat, keperluan, tujuan)
"""
import json
import sys
import time
import urllib.error
import urllib.request

from config import Config

OK, GAGAL = '[OK]   ', '[GAGAL]'


def _root_url():
    base = Config.LLM_BASE_URL.rstrip('/')
    return base[:-3] if base.endswith('/v1') else base


def main() -> int:
    print('=== Cek LLM untuk asisten AI surat RTConnect ===\n')
    if not Config.LLM_BASE_URL:
        print(f'{GAGAL} LLM_BASE_URL kosong -> asisten AI surat memakai Gemini, bukan LLM lokal.')
        print('        Isi LLM_BASE_URL, contoh: http://192.168.88.217:11434/v1')
        return 1
    print(f'        LLM_BASE_URL         = {Config.LLM_BASE_URL}')
    print(f'        LLM_MODEL            = {Config.LLM_MODEL}')
    print(f'        LLM_TIMEOUT_SECONDS  = {Config.LLM_TIMEOUT_SECONDS:.0f}')
    if Config.LLM_TIMEOUT_SECONDS < 60:
        print('        Saran: set LLM_TIMEOUT_SECONDS=120 (model pertama kali dimuat bisa 10-30 detik)')

    # 2. Daftar model (endpoint Ollama /api/tags)
    try:
        with urllib.request.urlopen(_root_url() + '/api/tags', timeout=15) as response:
            models = [m['name'] for m in json.loads(response.read().decode()).get('models', [])]
        print(f'\n{OK} Server LLM bisa dihubungi. Model terpasang: {", ".join(models) or "-"}')
    except Exception as error:  # noqa: BLE001 - pesan diagnosis untuk pengguna
        print(f'\n{GAGAL} Server LLM tidak bisa dihubungi: {error}')
        print('        Server Ollama kampus (192.168.88.x) hanya bisa diakses dari server Coolify.')
        print('        Untuk tes di laptop, pasang Ollama lalu isi LLM_BASE_URL=http://localhost:11434/v1')
        return 1

    # 3. Model tersedia?
    if models and Config.LLM_MODEL not in models:
        print(f'{GAGAL} Model "{Config.LLM_MODEL}" tidak ada di server. Ganti LLM_MODEL ke salah satu di atas.')
        return 1
    print(f'{OK} Model "{Config.LLM_MODEL}" tersedia.')

    # 4. Uji ekstraksi formulir lewat jalur yang sama dengan aplikasi
    from services import ai_fill_service
    letter_types = [
        {'jenis_surat_id': 1, 'kode_surat': 'SKCK', 'nama_surat': 'Surat Pengantar SKCK', 'persyaratan_dokumen': None},
        {'jenis_surat_id': 2, 'kode_surat': 'DOM', 'nama_surat': 'Surat Keterangan Domisili', 'persyaratan_dokumen': None},
        {'jenis_surat_id': 3, 'kode_surat': 'KTP', 'nama_surat': 'Surat Pengantar KTP', 'persyaratan_dokumen': None},
        {'jenis_surat_id': 4, 'kode_surat': 'SKU', 'nama_surat': 'Surat Keterangan Usaha', 'persyaratan_dokumen': None},
    ]
    cerita = 'Saya mau bikin SKCK buat melamar kerja di PT Maju Jaya, suratnya untuk Polrestabes'
    print(f'\n        Uji cerita: "{cerita}"')
    start = time.time()
    hasil = ai_fill_service.suggest_application(cerita, letter_types, stored={})
    detik = time.time() - start
    if not hasil['ai_digunakan']:
        print(f'{GAGAL} AI tidak dipakai ({detik:.1f} detik). Lihat pesan "Asisten AI tidak dipakai" di log di atas.')
        return 1
    jenis = (hasil['jenis_surat'] or {}).get('kode_surat')
    print(f'{OK} Model {hasil["model"]} menjawab dalam {detik:.1f} detik')
    print(f'        jenis surat : {jenis}')
    print(f'        keperluan   : {hasil["keperluan"]}')
    print(f'        tujuan      : {hasil["data_pemohon"].get("tujuan")}')
    if hasil.get('ditolak'):
        print(f'        ditolak     : {hasil["ditolak"]}')
    if jenis != 'SKCK':
        print('        Catatan: jenis surat seharusnya SKCK. Model kurang tepat, coba model lain.')
    return 0


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s: %(message)s')
    sys.exit(main())
