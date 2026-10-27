"""
Chatbot Service & RAG Cache Validator Module
Menyediakan validasi integritas cache embedding (AUD-10), sinkronisasi otomatis,
dan layanan akses chatbot knowledge base.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

CHATBOT_DIR = Path(__file__).parent
DATASET_PATH = CHATBOT_DIR / "dataset" / "knowledgebase.jsonl"
CACHE_DIR = CHATBOT_DIR / "cache"
CACHE_EMBEDDINGS_PATH = CACHE_DIR / "embeddings.npy"
CACHE_IDS_PATH = CACHE_DIR / "ids.json"
CACHE_METADATA_PATH = CACHE_DIR / "cache_metadata.json"


def hitung_hash_file(filepath: Path) -> Optional[str]:
    """Menghitung SHA-256 hexdigest dari file target."""
    if not filepath.exists():
        return None
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validasi_integritas_cache() -> Tuple[bool, str]:
    """
    Memvalidasi apakah cache embeddings.npy dan ids.json selaras
    dengan isi dokumen referensi di dataset knowledgebase.jsonl (AUD-10).
    
    Mengembalikan (is_valid: bool, reason: str).
    """
    if not DATASET_PATH.exists():
        return False, f"File dataset tidak ditemukan: {DATASET_PATH}"
    if not CACHE_EMBEDDINGS_PATH.exists():
        return False, f"File cache embedding tidak ditemukan: {CACHE_EMBEDDINGS_PATH}"
    if not CACHE_IDS_PATH.exists():
        return False, f"File cache ID tidak ditemukan: {CACHE_IDS_PATH}"

    try:
        from .preprocessing import baca_dataset, pilih_referensi
    except ImportError:
        try:
            from preprocessing import baca_dataset, pilih_referensi
        except ImportError:
            import sys
            sys.path.insert(0, str(CHATBOT_DIR))
            from preprocessing import baca_dataset, pilih_referensi

    try:
        data = baca_dataset()
        referensi = pilih_referensi(data)
        dataset_ids = [item["id"] for item in referensi]
    except Exception as e:
        return False, f"Gagal membaca dataset knowledgebase: {e}"

    try:
        with open(CACHE_IDS_PATH, "r", encoding="utf-8") as f:
            cached_ids = json.load(f)
    except Exception as e:
        return False, f"Gagal membaca cache ids.json: {e}"

    # 1. Periksa kesesuaian daftar dan urutan ID
    if cached_ids != dataset_ids:
        return False, f"Cache ID ({len(cached_ids)}) tidak cocok dengan ID referensi dataset ({len(dataset_ids)})."

    # 2. Periksa kesesuaian dimensi numpy jika numpy tersedia
    try:
        import numpy as np
        # Membaca header shape tanpa memuat seluruh array ke memory
        with open(CACHE_EMBEDDINGS_PATH, "rb") as npy_file:
            version = np.lib.format.read_magic(npy_file)
            shape, fortran_order, dtype = np.lib.format._read_array_header(npy_file, version)
            if shape[0] != len(dataset_ids):
                return False, f"Jumlah baris vektor ({shape[0]}) tidak sesuai jumlah dokumen ({len(dataset_ids)})."
    except Exception:
        pass

    # 3. Periksa metadata SHA-256 jika ada
    if CACHE_METADATA_PATH.exists():
        try:
            with open(CACHE_METADATA_PATH, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
            current_hash = hitung_hash_file(DATASET_PATH)
            if meta.get("dataset_sha256") and meta.get("dataset_sha256") != current_hash:
                return False, "Hash SHA-256 dataset knowledgebase telah berubah sejak embedding dibuat."
        except Exception:
            pass

    return True, "Cache embedding dan dataset referensi tersinkronisasi sempurna."


def pastikan_cache_tersinkronisasi(force_regenerate: bool = False) -> bool:
    """
    Memeriksa integritas cache embedding. Jika tidak valid atau force_regenerate=True,
    mencoba melakukan regenerasi otomatis (jika sentence-transformers tersedia)
    atau melempar exception deskriptif jika dependensi belum dipasang.
    """
    is_valid, reason = validasi_integritas_cache()
    if is_valid and not force_regenerate:
        logger.info("[RAG Cache] %s", reason)
        return True

    logger.warning("[RAG Cache Desinkronisasi] %s. Memulai regenerasi otomatis...", reason)
    try:
        try:
            from .embedding import generate_embeddings
        except ImportError:
            try:
                from embedding import generate_embeddings
            except ImportError:
                import sys
                sys.path.insert(0, str(CHATBOT_DIR))
                from embedding import generate_embeddings

        generate_embeddings(folder_output=CACHE_DIR)
        logger.info("[RAG Cache] Regenerasi embedding berhasil disimpan ke %s", CACHE_DIR)
        return True
    except RuntimeError as re_err:
        raise RuntimeError(
            f"Cache embedding RAG kedaluwarsa ({reason}), namun regenerasi otomatis gagal: {re_err}"
        ) from re_err
    except Exception as exc:
        raise RuntimeError(
            f"Gagal meregenerasi cache embedding RAG: {exc}"
        ) from exc
