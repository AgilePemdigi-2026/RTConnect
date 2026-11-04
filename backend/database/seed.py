import json
import os
from pathlib import Path

import bcrypt

from config import Config

try:
    from database.db import close_pool, execute, execute_returning, query_one
except ImportError:
    from db import close_pool, execute, execute_returning, query_one

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def _load_public_references():
    dataset_path = (
        Path(__file__).resolve().parent.parent
        / 'chatbot'
        / 'dataset'
        / 'knowledgebase.jsonl'
    )
    if not dataset_path.exists():
        print(f"  [!] Dataset referensi tidak ditemukan: {dataset_path}")
        return []

    documents = []
    with dataset_path.open('r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                documents.append(json.loads(line))

    return [
        document for document in documents
        if document.get('jenis_sumber') == 'pemerintah'
        and document.get('kelayakan_rag') == 'REFERENSI_PUBLIK_DENGAN_LABEL_INSTANSI'
    ]

def _seed_public_references(rt_id):
    references = _load_public_references()
    if not references:
        return 0, 0

    inserted = 0
    linked = 0
    for document in references:
        source_id = document.get('id')
        judul = document.get('judul')
        konten = document.get('konten')
        if not source_id or not judul or not konten:
            continue

        existing = query_one(
            "SELECT knowledge_id FROM knowledgebase WHERE judul = %s",
            (judul,),
        )
        if existing:
            # Dokumen lama mungkin dibuat sebelum kolom kode_sumber ada.
            execute_returning(
                """UPDATE knowledgechunk
                   SET kode_sumber = %s
                   WHERE knowledge_id = %s
                     AND (kode_sumber IS NULL OR kode_sumber = '')
                   RETURNING chunk_id""",
                (source_id, existing['knowledge_id']),
            )
            linked += 1
            continue

        kategori = (document.get('kategori') or 'referensi_publik')[:50]
        keywords = list(document.get('kata_kunci') or [])
        keywords.extend(document.get('contoh_pertanyaan') or [])
        kata_kunci = (' '.join(keywords) or judul)[:255]

        knowledge_id = execute_returning(
            """INSERT INTO knowledgebase
               (judul, kategori, isi_dokumen, sumber, uploaded_by)
               VALUES (%s, %s, %s, %s, %s) RETURNING knowledge_id""",
            (judul, kategori, konten, 'Referensi publik pemerintah', rt_id),
        )['knowledge_id']
        execute_returning(
            """INSERT INTO knowledgechunk
               (knowledge_id, urutan_chunk, isi_chunk, kata_kunci, kode_sumber)
               VALUES (%s, %s, %s, %s, %s) RETURNING chunk_id""",
            (knowledge_id, 1, konten, kata_kunci, source_id),
        )
        inserted += 1

    return inserted, linked

def seed_database(include_demo_users=None):
    if include_demo_users is None:
        include_demo_users = os.getenv('SEED_DEMO_USERS', '').lower() == 'true'
    if include_demo_users and Config.IS_PRODUCTION:
        raise RuntimeError('Demo users must never be seeded in production.')

    print("=== Memulai seeding data RTConnect ke Supabase (PostgreSQL) ===")

    # 1. Master Jenis Surat
    surat_types = [
        ('DOM', 'Surat Keterangan Domisili', f'Surat Keterangan Domisili Warga {Config.RT_AREA}', 'KTP dan Bukti Tempat Tinggal (PBB/Sewa)'),
        ('KTP', 'Surat Pengantar KTP Baru / Perpanjangan', 'Surat Pengantar Pengurusan KTP-el ke Kelurahan/Kecamatan', 'Fotokopi Kartu Keluarga dan KTP Lama'),
        ('SKCK', 'Surat Pengantar SKCK', 'Surat Pengantar Pembuatan Catatan Kepolisian', 'KTP Asli dan Kartu Keluarga'),
        ('SKU', 'Surat Keterangan Usaha', 'Surat Keterangan Domisili Usaha Mikro Warga', 'Foto Tempat Usaha dan KTP Pemilik')
    ]

    for kode, nama, template, syarat in surat_types:
        existing = query_one("SELECT jenis_surat_id FROM jenissurat WHERE kode_surat = %s", (kode,))
        if not existing:
            execute_returning(
                """INSERT INTO jenissurat (kode_surat, nama_jenis, template_surat, persyaratan_dokumen, butuh_ttd_basah)
                   VALUES (%s, %s, %s, %s, %s) RETURNING jenis_surat_id""",
                (kode, nama, template, syarat, False)
            )
            print(f"  [+] Jenis Surat: {nama}")

    # Demo accounts exist only for local development and isolated CI databases.
    if include_demo_users:
        seed_assets_dir = os.path.join(os.path.dirname(__file__), 'seed_assets')
        signatures_dir = Config.SIGNATURES_FOLDER
        os.makedirs(signatures_dir, exist_ok=True)
        if os.path.exists(seed_assets_dir):
            import shutil
            for filename in os.listdir(seed_assets_dir):
                src = os.path.join(seed_assets_dir, filename)
                dest = os.path.join(signatures_dir, filename)
                if os.path.isfile(src) and not os.path.exists(dest):
                    shutil.copy2(src, dest)
                    print(f"  [+] Copied seed signature: {filename}")

        default_users = [
            ('0000000000000001', 'Test RT User', 'rt@example.test', 'LocalTestOnly#2026',
             '0000000000', 'Alamat RT untuk pengujian', 'rt', 'signatures/rt_indra_signature.png'),
            ('0000000000000002', 'Test Resident', 'resident@example.test', 'LocalTestOnly#2026',
             '0000000000', 'Alamat warga untuk pengujian', 'warga', 'signatures/warga_dafin_signature.png'),
        ]
        for nik, nama, email, password, phone, alamat, role, sig_key in default_users:
            table = 'rt' if role == 'rt' else 'warga'
            id_col = 'rt_id' if role == 'rt' else 'warga_id'
            existing = query_one(f"SELECT {id_col}, nik, tanda_tangan_digital FROM {table} WHERE lower(email) = lower(%s) OR nik = %s", (email, nik))
            if not existing:
                if role == 'rt':
                    execute_returning(
                        """INSERT INTO rt (nik, nama, jabatan, email, password_hash, no_telp, nomor_rt, nomor_rw, tanda_tangan_digital)
                           VALUES (%s, %s, 'Ketua RT', %s, %s, %s, %s, %s, %s) RETURNING rt_id""",
                        (nik, nama, email, hash_password(password), phone, Config.RT_NUMBER, Config.RW_NUMBER, sig_key)
                    )
                else:
                    execute_returning(
                        """INSERT INTO warga (nik, nama, email, password_hash, no_telp, alamat, nomor_rt, nomor_rw, tanda_tangan_digital)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING warga_id""",
                        (nik, nama, email, hash_password(password), phone, alamat, Config.RT_NUMBER, Config.RW_NUMBER, sig_key)
                    )
                print(f"  [+] Development-only user: {nama} ({role.upper()})")
            elif not existing.get('tanda_tangan_digital'):
                execute(
                    f"UPDATE {table} SET tanda_tangan_digital = %s WHERE {id_col} = %s",
                    (sig_key, existing[id_col])
                )
                print(f"  [+] Updated development signature for: {nama}")

    # 3. Knowledge base for lexical Tanya RT search
    rt_user = query_one("SELECT rt_id FROM rt ORDER BY rt_id LIMIT 1")
    rt_id = rt_user['rt_id'] if rt_user else None

    bylaws = [
        (
            f'Pedoman Tata Tertib & Layanan Surat {Config.RT_AREA}',
            'administrasi',
            f'1. Surat pengantar {Config.RT_AREA} berlaku selama 30 hari kalender sejak tanggal pengesahan.\n'
            '2. Untuk pembuatan surat domisili, warga wajib menyiapkan KTP asli dan bukti tempat tinggal.\n'
            '3. Warga yang mengurus surat keterangan usaha (SKU) wajib melampirkan foto tempat usaha fisik.\n'
            f'4. Pelayanan surat tanda tangan basah dapat diambil di rumah Ketua RT ({Config.RT_OFFICE_ADDRESS}) '
            'pada jam 18.30 - 21.00 WIB setiap hari kerja.'
        ),
        (
            f'Ketentuan Iuran Lingkungan & Fasilitas Umum {Config.RT_AREA}',
            'fasum',
            f'1. Iuran kas kebersihan dan keamanan {Config.RT_AREA} dibayarkan paling lambat tanggal 10 setiap bulannya.\n'
            f'2. Penggunaan balai warga di {Config.RT_AREA} untuk hajatan atau acara warga wajib melapor kepada Ketua RT minimal 7 hari sebelumnya.\n'
            f'3. Kerja bakti saluran air dan kebersihan {Config.RT_AREA} dilaksanakan setiap hari Minggu pertama awal bulan.'
        )
    ]

    for judul, kategori, isi in bylaws:
        existing = query_one("SELECT knowledge_id FROM knowledgebase WHERE judul = %s", (judul,))
        if not existing:
            kb_id = execute_returning(
                "INSERT INTO knowledgebase (judul, kategori, isi_dokumen, sumber, uploaded_by) VALUES (%s, %s, %s, %s, %s) RETURNING knowledge_id",
                (judul, kategori, isi, f'Tata tertib {Config.RT_AREA}', rt_id)
            )['knowledge_id']
            print(f"  [+] Knowledge Base: {judul}")

            # Chunking Dokumen
            lines = [line.strip() for line in isi.split('\n') if line.strip()]
            for idx, chunk in enumerate(lines):
                execute_returning(
                    "INSERT INTO knowledgechunk (knowledge_id, urutan_chunk, isi_chunk, kata_kunci) VALUES (%s, %s, %s, %s) RETURNING chunk_id",
                    (kb_id, idx + 1, chunk, judul)
                )

    # 4. Referensi publik pemerintah untuk pertanyaan KTP/KK/SKCK/NIB.
    inserted, linked = _seed_public_references(rt_id)
    print(
        f"  [+] Referensi publik: {inserted} dokumen baru, "
        f"{linked} dokumen lama ditautkan metadata sumbernya"
    )

    print("[SUCCESS] Seeding basis data RTConnect berhasil!")

if __name__ == '__main__':
    try:
        seed_database()
    finally:
        close_pool()