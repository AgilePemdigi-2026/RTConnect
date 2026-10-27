import hashlib
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


def teks_dokumen(item):
    return f"{item['judul']}. {item['konten']}"


def contoh_dokumen(item):
    return [
        str(c).strip()
        for c in (item.get("contoh_pertanyaan") or [])
        if str(c).strip()
    ]


def hitung_hash(referensi):
    """Sidik jari isi dataset + model. Berubah jika teks diedit."""
    bahan = [MODEL] + [
        [
            item["id"],
            item["judul"],
            item["konten"],
            contoh_dokumen(item),
        ]
        for item in referensi
    ]

    return hashlib.sha256(
        json.dumps(
            bahan,
            ensure_ascii=False,
            sort_keys=True
        ).encode("utf-8")
    ).hexdigest()


def bangun_embedding():
    referensi = pilih_referensi(baca_dataset())

    if not referensi:
        raise ValueError(
            "Tidak ada referensi pemerintah yang layak dipakai"
        )

    model = SentenceTransformer(MODEL)

    # 1. Embedding dokumen (judul + konten)
    vektor_dokumen = model.encode(
        [teks_dokumen(item) for item in referensi],
        normalize_embeddings=True,
        show_progress_bar=True
    )

    # 2. Embedding contoh pertanyaan (pertanyaan vs pertanyaan)
    contoh_teks = []
    contoh_indeks = []

    for i, item in enumerate(referensi):
        for contoh in contoh_dokumen(item):
            contoh_teks.append(contoh)
            contoh_indeks.append(i)

    if contoh_teks:
        vektor_contoh = model.encode(
            contoh_teks,
            normalize_embeddings=True,
            show_progress_bar=False
        )
    else:
        vektor_contoh = np.zeros(
            (0, vektor_dokumen.shape[1]),
            dtype=vektor_dokumen.dtype
        )

    CACHE.mkdir(exist_ok=True)

    np.save(CACHE / "embeddings.npy", vektor_dokumen)
    np.save(CACHE / "contoh_embeddings.npy", vektor_contoh)

    (CACHE / "ids.json").write_text(
        json.dumps(
            [item["id"] for item in referensi],
            indent=2
        ),
        encoding="utf-8"
    )

    (CACHE / "contoh_indeks.json").write_text(
        json.dumps(contoh_indeks),
        encoding="utf-8"
    )

    (CACHE / "meta.json").write_text(
        json.dumps(
            {
                "model": MODEL,
                "hash": hitung_hash(referensi),
                "jumlah_dokumen": len(referensi),
                "jumlah_contoh": len(contoh_teks),
            },
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Embedding tersimpan: {len(referensi)} dokumen, "
        f"{len(contoh_teks)} contoh pertanyaan, "
        f"dimensi {vektor_dokumen.shape[1]}"
    )


if __name__ == "__main__":
    bangun_embedding()