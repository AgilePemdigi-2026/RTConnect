
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from .preprocessing import baca_dataset, pilih_referensi
except ImportError:
    from preprocessing import baca_dataset, pilih_referensi


MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CACHE = Path(__file__).parent / "cache"


def bangun_embedding():
    referensi = pilih_referensi(baca_dataset())

    if not referensi:
        raise ValueError(
            "Tidak ada referensi pemerintah yang layak dipakai"
        )

    teks = [
        f"{item['judul']}. {item['konten']}"
        for item in referensi
    ]

    model = SentenceTransformer(MODEL)

    vektor = model.encode(
        teks,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    CACHE.mkdir(exist_ok=True)

    np.save(CACHE / "embeddings.npy", vektor)

    (CACHE / "ids.json").write_text(
        json.dumps(
            [item["id"] for item in referensi],
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Embedding tersimpan: {len(referensi)} dokumen, "
        f"dimensi {vektor.shape[1]}"
    )


if __name__ == "__main__":
    bangun_embedding()
