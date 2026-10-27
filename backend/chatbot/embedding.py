import hashlib
import json
from pathlib import Path

def generate_embeddings(folder_output=None):
    """
    Menghasilkan vektor embedding untuk dokumen referensi knowledge base
    dan menyimpannya ke folder cache beserta metadata hash.
    """
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise RuntimeError(
            "Dependensi sentence-transformers atau numpy belum terpasang. "
            "Jalankan: pip install sentence-transformers numpy"
        ) from e

    try:
        from .preprocessing import baca_dataset, pilih_referensi
    except ImportError:
        try:
            from preprocessing import baca_dataset, pilih_referensi
        except ImportError:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from preprocessing import baca_dataset, pilih_referensi

    data = baca_dataset()
    referensi = pilih_referensi(data)
    teks = [
        f"{item['judul']}. {item['konten']}"
        for item in referensi
    ]

    # Model embedding
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    embeddings = model.encode(
        teks,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    if folder_output is None:
        folder_output = Path(__file__).parent / "cache"
    folder_output = Path(folder_output)
    folder_output.mkdir(exist_ok=True)

    # Simpan hasil embedding
    np.save(folder_output / "embeddings.npy", embeddings)

    # Simpan ID dokumen
    ids = [item["id"] for item in referensi]
    with open(folder_output / "ids.json", "w", encoding="utf-8") as file:
        json.dump(ids, file, indent=2)

    # Simpan metadata SHA-256 dataset untuk validasi otomatis
    dataset_file = Path(__file__).parent / "dataset" / "knowledgebase.jsonl"
    if dataset_file.exists():
        with open(dataset_file, "rb") as df:
            dataset_hash = hashlib.sha256(df.read()).hexdigest()
        metadata = {
            "dataset_sha256": dataset_hash,
            "total_documents": len(teks),
            "ids": ids
        }
        with open(folder_output / "cache_metadata.json", "w", encoding="utf-8") as mf:
            json.dump(metadata, mf, indent=2)

    print("Jumlah dokumen:", len(teks))
    print("Ukuran embedding:", embeddings.shape)
    print("Embedding berhasil disimpan")
    return embeddings, ids

if __name__ == "__main__":
    generate_embeddings()
