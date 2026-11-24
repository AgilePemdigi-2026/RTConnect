"""Skrip Backfill Embedding Vektor TanyaRT (PostgreSQL/Supabase).

Mengisi kolom 'embedding_vector' (jsonb) pada tabel 'knowledgechunk'
menggunakan layanan embedding resmi proyek (text-embedding-3-small via OpenAI).

Karakteristik & Keamanan:
- Standar mode adalah DRY-RUN (tidak melakukan panggilan API berbayar dan tidak menulis DB).
- Menampilkan target tabel, jumlah chunk (27 chunks), dan teks sumber per chunk untuk persetujuan.
- Mempertahankan chunk_id yang sudah ada dan tidak merusak relasi foreign key pada 'retrievallog'.
- Menangani kegagalan API secara aman (misal HTTP 429 kuota habis) tanpa membocorkan API key.
- Eksekusi tulis nyata HANYA dilakukan jika argumen '--apply' disertakan secara eksplisit.

Penggunaan:
    cd backend
    python -m database.backfill_embeddings           # Default DRY-RUN
    python -m database.backfill_embeddings --apply   # Mode Eksekusi Nyata
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Setup path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from config import Config
from database.db import close_pool, execute, query_all, query_one
from services.semantic_embedding_service import (
    EMBEDDING_DIMENSION,
    EmbeddingServiceUnavailableError,
    generate_embedding,
    is_embedding_configured,
)

logger = logging.getLogger(__name__)


def get_chunks_for_backfill():
    """Ambil seluruh chunk dari database beserta judul dokumen."""
    return query_all("""
        SELECT c.chunk_id, c.knowledge_id, c.urutan_chunk, c.isi_chunk,
               c.kata_kunci, c.kode_sumber,
               (c.embedding_vector IS NOT NULL) AS has_vector,
               k.judul AS judul_dokumen, k.kategori
        FROM knowledgechunk c
        JOIN knowledgebase k ON c.knowledge_id = k.knowledge_id
        ORDER BY c.chunk_id ASC
    """)


def run_backfill(apply_changes: bool = False, limit: int | None = None):
    print("=" * 80)
    print("TANYART KNOWLEDGE BASE EMBEDDING BACKFILL UTILITY")
    print(f"Mode Operasi: {'[APPLY - TULIS DATABASE AKTIF]' if apply_changes else '[DRY-RUN - HANYA SIMULASI & INSPEKSI]'}")
    print("=" * 80)

    # 1. Periksa konfigurasi API embedding
    api_configured = is_embedding_configured()
    print(f"Layanan Embedding Proyek : {Config.EMBEDDING_MODEL}")
    print(f"Dimensi Vektor Target    : {EMBEDDING_DIMENSION}")
    print(f"Status Kunci API         : {'Terkonfigurasi' if api_configured else 'BELUM DIKONFIGURASI'}")

    # Uji coba koneksi API embedding secara aman hanya dilakukan jika mode apply aktif
    api_ready = False
    api_error_detail = None
    if apply_changes and api_configured:
        print("\nMemeriksa status ketersediaan API Embedding...")
        try:
            sample_vec = generate_embedding("uji coba ketersediaan embedding", timeout=5.0)
            if len(sample_vec) == EMBEDDING_DIMENSION:
                api_ready = True
                print("  [OK] Panggilan embedding berhasil. Layanan siap digunakan.")
        except EmbeddingServiceUnavailableError as err:
            err_msg = str(err)
            if "429" in err_msg or "credits" in err_msg.lower() or "quota" in err_msg.lower():
                api_error_detail = "HTTP 429: Kuota API habis (Insufficient Quota / No credits remaining)."
            else:
                api_error_detail = f"Gagal menghubungi API ({type(err).__name__})"
            print(f"  [X] API TIDAK DAPAT DIGUNAKAN: {api_error_detail}")
        except Exception as err:
            api_error_detail = f"Kesalahan tidak terduga ({type(err).__name__})"
            print(f"  [X] {api_error_detail}")

    # 2. Ambil data chunk dari database secara read-only
    try:
        chunks = get_chunks_for_backfill()
    except Exception as err:
        print(f"\n[ERROR] Gagal membaca database: tidak dapat mengambil data ({type(err).__name__})")
        return 1

    total_chunks = len(chunks)
    chunks_without_vec = [c for c in chunks if not c["has_vector"]]
    chunks_with_vec = [c for c in chunks if c["has_vector"]]

    print(f"\nTarget Database Table    : public.knowledgechunk")
    print(f"Total Potongan Dokumen   : {total_chunks} chunk")
    print(f"Sudah Memiliki Vektor    : {len(chunks_with_vec)} chunk")
    print(f"Belum Memiliki Vektor    : {len(chunks_without_vec)} chunk")

    if limit and limit > 0:
        chunks_to_process = chunks_without_vec[:limit]
        print(f"Dibatasi memproses       : {limit} chunk pertama")
    else:
        chunks_to_process = chunks_without_vec

    # 3. Tampilkan daftar teks sumber yang akan diproses
    print("\n" + "-" * 80)
    print("DAFTAR TEKS SUMBER POTONGAN DOKUMEN YANG AKAN DIPROSES:")
    print("-" * 80)
    for idx, c in enumerate(chunks_to_process, start=1):
        source_label = f"[{c['kode_sumber']}]" if c["kode_sumber"] else "[LOKAL]"
        combined_text = f"{c['judul_dokumen']}. {c['isi_chunk']}"
        preview = combined_text[:120] + ("..." if len(combined_text) > 120 else "")
        print(f"{idx:2d}. Chunk #{c['chunk_id']:2d} {source_label:<10} | {preview}")

    print("-" * 80)

    # 4. Evaluasi eksekusi
    if not apply_changes:
        print("\n[SELESAI DRY-RUN] Tidak ada panggilan API berbayar dan tidak ada penulisan database.")
        print("Untuk menjalankan backfill nyata setelah kuota API tersedia:")
        print("    python -m database.backfill_embeddings --apply")
        return 0

    if not api_ready:
        print(f"\n[BATAL] Backfill dibatalkan karena API embedding tidak siap: {api_error_detail}")
        print("Silakan isi kuota OpenAI API atau atur OPENAI_API_KEY yang aktif terlebih dahulu.")
        return 1

    if not chunks_to_process:
        print("\n[INFO] Seluruh potongan dokumen sudah memiliki embedding vector. Tidak ada yang perlu diisi.")
        return 0

    # 5. Eksekusi nyata jika disetujui (--apply dan api_ready)
    print(f"\nMemulai proses backfill untuk {len(chunks_to_process)} chunk...")
    success_count = 0
    fail_count = 0

    for idx, c in enumerate(chunks_to_process, start=1):
        chunk_id = c["chunk_id"]
        text_to_embed = f"{c['judul_dokumen']}. {c['isi_chunk']}"
        try:
            vec = generate_embedding(text_to_embed, timeout=10.0)
            vec_json = json.dumps(vec)
            execute(
                "UPDATE knowledgechunk SET embedding_vector = %s WHERE chunk_id = %s",
                (vec_json, chunk_id),
            )
            success_count += 1
            print(f"  [{idx}/{len(chunks_to_process)}] Sukses Chunk #{chunk_id} ({c.get('kode_sumber') or 'lokal'})")
        except Exception as err:
            fail_count += 1
            print(f"  [{idx}/{len(chunks_to_process)}] GAGAL Chunk #{chunk_id}: {type(err).__name__}")
            if "429" in str(err) or "quota" in str(err).lower():
                print("  [X] Kuota habis di tengah proses. Menghentikan batch.")
                break

    print("\n" + "=" * 80)
    print(f"HASIL BACKFILL: {success_count} berhasil, {fail_count} gagal.")
    print("=" * 80)
    return 0 if fail_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Backfill embedding vektor pada knowledgechunk Supabase.")
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Jalankan penulisan ke database. Default adalah False (dry-run).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Batasi jumlah chunk yang diproses.",
    )
    args = parser.parse_args()

    try:
        sys.exit(run_backfill(apply_changes=args.apply, limit=args.limit))
    finally:
        close_pool()


if __name__ == "__main__":
    main()
