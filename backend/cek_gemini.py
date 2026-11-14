"""Cek cepat asisten AI (Gemini) tanpa menjalankan server.

Jalankan dari folder backend:
    python cek_gemini.py "Saya mau bikin surat pengantar SKCK buat melamar kerja di PT ABC"
"""

import json
import sys

from config import Config
from services.ai_fill_service import _call_gemini, mask_sensitive

CONTOH_JENIS = [
    {'jenis_surat_id': 1, 'kode_surat': 'DOM', 'nama_surat': 'Surat Keterangan Domisili'},
    {'jenis_surat_id': 2, 'kode_surat': 'KTP', 'nama_surat': 'Surat Pengantar KTP/KK'},
    {'jenis_surat_id': 3, 'kode_surat': 'SKCK', 'nama_surat': 'Surat Pengantar SKCK'},
    {'jenis_surat_id': 4, 'kode_surat': 'SKU', 'nama_surat': 'Surat Keterangan Usaha'},
]

if __name__ == '__main__':
    pesan = ' '.join(sys.argv[1:]) or 'Saya mau bikin surat pengantar SKCK buat melamar kerja di PT ABC'
    if not Config.GEMINI_API_KEY:
        sys.exit('[X] GEMINI_API_KEY belum diisi di backend/.env')
    print(f'Model : {Config.GEMINI_MODEL}')
    print(f'Pesan : {mask_sensitive(pesan)}\n')
    try:
        hasil = _call_gemini(mask_sensitive(pesan), CONTOH_JENIS)
    except Exception as error:
        sys.exit(f'[X] Gagal memanggil Gemini: {type(error).__name__}: {error}')
    print(json.dumps(hasil, indent=2, ensure_ascii=False))
    print('\n[OK] Gemini berhasil dipanggil.')
