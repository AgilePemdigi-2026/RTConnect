
import json
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

try:
    from .preprocessing import baca_dataset, pilih_referensi
    from .embedding import MODEL
    from .rules import (
        tokenisasi,
        topik_pertanyaan,
        aksi_pertanyaan,
        topik_dokumen,
        aksi_dokumen,
    )
except ImportError:
    from preprocessing import baca_dataset, pilih_referensi
    from embedding import MODEL
    from rules import (
        tokenisasi,
        topik_pertanyaan,
        aksi_pertanyaan,
        topik_dokumen,
        aksi_dokumen,
    )


CACHE = Path(__file__).parent / "cache"


class HybridRetriever:

    def __init__(self):
        referensi = pilih_referensi(baca_dataset())

        if not referensi:
            raise ValueError(
                "Tidak ada referensi pemerintah dalam dataset"
            )

        ids = json.loads(
            (CACHE / "ids.json").read_text(
                encoding="utf-8"
            )
        )

        vektor = np.load(
            CACHE / "embeddings.npy",
            allow_pickle=False
        )

        kamus = {
            item["id"]: item
            for item in referensi
        }

        if (
            len(ids) != len(set(ids))
            or set(ids) != set(kamus)
            or len(ids) != len(vektor)
        ):
            raise ValueError(
                "Cache tidak cocok dengan dataset. "
                "Jalankan embedding.py lagi."
            )

        self.dokumen = [
            kamus[id_dokumen]
            for id_dokumen in ids
        ]

        self.embeddings = vektor
        self.model = SentenceTransformer(MODEL)

        # BM25 dibuat sekali dari seluruh referensi
        korpus = []

        for item in self.dokumen:
            teks = " ".join([
                item["judul"],
                item["judul"],
                item.get("kategori", ""),
                item["konten"],
                " ".join(
                    item.get("kata_kunci") or []
                ),
                " ".join(
                    item.get("contoh_pertanyaan") or []
                ),
            ])

            korpus.append(tokenisasi(teks))

        self.bm25 = BM25Okapi(korpus)

    def cari(self, pertanyaan, top_k=3):

        # 1. Semantic Search
        vektor = self.model.encode(
            [pertanyaan],
            normalize_embeddings=True
        )[0]

        cosine = self.embeddings @ vektor

        # 2. BM25
        bm25 = self.bm25.get_scores(
            tokenisasi(pertanyaan)
        )

        bm25 = np.maximum(bm25, 0)

        # 3. Reciprocal Rank Fusion
        skor_rrf = np.zeros(len(self.dokumen))

        ranking_semantik = np.argsort(
            -cosine,
            kind="stable"
        )

        for posisi, indeks in enumerate(
            ranking_semantik,
            start=1
        ):
            skor_rrf[indeks] += 1 / (60 + posisi)

        if np.any(bm25 > 0):

            ranking_bm25 = np.argsort(
                -bm25,
                kind="stable"
            )

            for posisi, indeks in enumerate(
                ranking_bm25,
                start=1
            ):
                if bm25[indeks] > 0:
                    skor_rrf[indeks] += 1 / (60 + posisi)

        # 4. Prioritas topik dan keperluan
        topik = topik_pertanyaan(pertanyaan)
        aksi = aksi_pertanyaan(pertanyaan)

        skor_akhir = skor_rrf.copy()

        for i, item in enumerate(self.dokumen):

            if (
                topik is not None
                and topik_dokumen(item) == topik
            ):
                skor_akhir[i] += 0.010

                if (
                    aksi is not None
                    and aksi_dokumen(item) == aksi
                ):
                    skor_akhir[i] += 0.004

        # 5. Mengurutkan hasil
        urutan = sorted(
            range(len(skor_akhir)),
            key=lambda i: (
                -skor_akhir[i],
                -cosine[i]
            )
        )[:top_k]

        hasil = []

        for i in urutan:
            item = self.dokumen[i]

            hasil.append({
                "id": item["id"],
                "judul": item["judul"],
                "konten": item["konten"],
                "sumber": item.get("url_sumber", ""),
                "topik": topik_dokumen(item),
                "aksi": aksi_dokumen(item),
                "skor": float(cosine[i]),
                "bm25": float(bm25[i]),
                "rrf": float(skor_rrf[i]),
                "skor_ranking": float(skor_akhir[i])
            })

        return hasil


if __name__ == "__main__":

    mesin = HybridRetriever()

    pertanyaan = input("Pertanyaan: ").strip()

    if pertanyaan:
        hasil = mesin.cari(pertanyaan)

        for item in hasil:
            print(
                f"{item['id']} | {item['judul']} | "
                f"Cosine {item['skor']:.4f} | "
                f"BM25 {item['bm25']:.4f} | "
                f"RRF {item['rrf']:.4f}"
            )
