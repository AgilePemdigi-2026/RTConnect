import json
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

try:
    from .preprocessing import baca_dataset, pilih_referensi
    from .embedding import MODEL, hitung_hash
    from .rules import (
        normalisasi,
        tokenisasi_bm25,
        semua_topik,
        aksi_pertanyaan,
        topik_dokumen,
        aksi_dokumen,
    )
except ImportError:
    from preprocessing import baca_dataset, pilih_referensi
    from embedding import MODEL, hitung_hash
    from rules import (
        normalisasi,
        tokenisasi_bm25,
        semua_topik,
        aksi_pertanyaan,
        topik_dokumen,
        aksi_dokumen,
    )

CACHE = Path(__file__).parent / "cache"

K_RRF = 60

# CATATAN: dengan korpus kecil, selisih RRF terbesar antar dokumen
# hanya sekitar 0,008. Bonus topik 0,010 karena itu berfungsi sebagai
# PRIORITAS TOPIK (dokumen bertopik cocok selalu di atas). Bonus aksi
# 0,004 masih bisa dikalahkan oleh skor pencarian.
BONUS_TOPIK = 0.010
BONUS_AKSI = 0.004

MODE = {"semantic", "bm25", "hybrid", "hybrid_aturan"}


def _peringkat(skor, hanya_positif=False):
    """Posisi 1..n tiap dokumen. Skor <= 0 tidak diberi posisi
    jika hanya_positif=True (posisi = n + 1)."""
    n = len(skor)
    urutan = np.argsort(-skor, kind="stable")
    posisi = np.empty(n, dtype=int)
    posisi[urutan] = np.arange(1, n + 1)

    if hanya_positif:
        posisi[skor <= 0] = n + 1

    return posisi


class HybridRetriever:

    def __init__(self):
        referensi = pilih_referensi(baca_dataset())

        if not referensi:
            raise ValueError(
                "Tidak ada referensi pemerintah dalam dataset"
            )

        try:
            ids = json.loads(
                (CACHE / "ids.json").read_text(encoding="utf-8")
            )
            meta = json.loads(
                (CACHE / "meta.json").read_text(encoding="utf-8")
            )
            vektor = np.load(
                CACHE / "embeddings.npy",
                allow_pickle=False
            )
            vektor_contoh = np.load(
                CACHE / "contoh_embeddings.npy",
                allow_pickle=False
            )
            contoh_indeks = json.loads(
                (CACHE / "contoh_indeks.json").read_text(
                    encoding="utf-8"
                )
            )
        except FileNotFoundError as galat:
            raise ValueError(
                "Cache embedding belum lengkap "
                f"({galat.filename}). Jalankan embedding.py."
            ) from galat

        kamus = {item["id"]: item for item in referensi}

        if (
            len(ids) != len(set(ids))
            or set(ids) != set(kamus)
            or len(ids) != len(vektor)
            or len(contoh_indeks) != len(vektor_contoh)
        ):
            raise ValueError(
                "Cache tidak cocok dengan dataset. "
                "Jalankan embedding.py lagi."
            )

        # Isi dokumen/model berubah walau ID sama -> cache basi
        if meta.get("hash") != hitung_hash(referensi):
            raise ValueError(
                "Isi dataset atau model berubah sejak embedding "
                "dibuat. Jalankan embedding.py lagi."
            )

        self.dokumen = [kamus[i] for i in ids]
        self.embeddings = vektor
        self.contoh_vektor = vektor_contoh
        self.contoh_indeks = np.array(contoh_indeks, dtype=int)
        self.model = SentenceTransformer(MODEL)

        # BM25 dibuat sekali dari seluruh referensi
        korpus = []

        for item in self.dokumen:
            teks = " ".join([
                item["judul"],
                item["judul"],
                item.get("kategori", ""),
                item["konten"],
                " ".join(item.get("kata_kunci") or []),
                " ".join(item.get("contoh_pertanyaan") or []),
            ])

            korpus.append(tokenisasi_bm25(teks))

        self.bm25 = BM25Okapi(korpus)

    def cari(self, pertanyaan, top_k=3, mode="hybrid_aturan"):

        if mode not in MODE:
            raise ValueError(f"mode harus salah satu dari {MODE}")

        n = len(self.dokumen)

                # 1. Semantic: dokumen + contoh pertanyaan.
        # Pertanyaan asli dan versi ternormalisasi (retak -> rusak,
        # e-KTP -> ktp, dst.) sama-sama di-encode; skor terbaik dipakai.
        teks_tanya = [pertanyaan]
        normal = normalisasi(pertanyaan)

        if normal != pertanyaan.lower():
            teks_tanya.append(normal)

        vektor_tanya = self.model.encode(
            teks_tanya,
            normalize_embeddings=True
        )

        cosine_dokumen = (self.embeddings @ vektor_tanya.T).max(axis=1)

        cosine_contoh = np.zeros(n)

        if len(self.contoh_vektor):
            kemiripan = (self.contoh_vektor @ vektor_tanya.T).max(axis=1)
            terbaik = np.full(n, -1.0)
            np.maximum.at(
                terbaik,
                self.contoh_indeks,
                kemiripan
            )
            cosine_contoh = np.maximum(terbaik, 0.0)

        semantik = np.maximum(cosine_dokumen, cosine_contoh)

        # 2. BM25
        bm25 = np.maximum(
            self.bm25.get_scores(tokenisasi_bm25(pertanyaan)),
            0
        )

        rank_semantik = _peringkat(semantik)
        rank_bm25 = _peringkat(bm25, hanya_positif=True)

        # 3. Reciprocal Rank Fusion
        skor_rrf = 1 / (K_RRF + rank_semantik)
        ada_bm25 = rank_bm25 <= n
        skor_rrf = skor_rrf + np.where(
            ada_bm25,
            1 / (K_RRF + rank_bm25),
            0.0
        )

        # 4. Prioritas topik dan keperluan
        topik = semua_topik(pertanyaan)
        aksi = aksi_pertanyaan(pertanyaan)

        bonus = np.zeros(n)

        if mode == "hybrid_aturan":
            for i, item in enumerate(self.dokumen):
                if topik and topik_dokumen(item) in topik:
                    bonus[i] += BONUS_TOPIK

                    if (
                        aksi is not None
                        and aksi_dokumen(item) == aksi
                    ):
                        bonus[i] += BONUS_AKSI

        if mode == "semantic":
            skor_akhir = semantik.copy()
        elif mode == "bm25":
            skor_akhir = bm25 + 1e-6 * semantik
        else:
            skor_akhir = skor_rrf + bonus

        urutan = sorted(
            range(n),
            key=lambda i: (-skor_akhir[i], -semantik[i])
        )[:top_k]

        hasil = []

        for i in urutan:
            item = self.dokumen[i]

            hasil.append({
                "id": item["id"],
                "judul": item["judul"],
                "konten": item["konten"],
                "sumber": item.get("url_sumber", ""),
                "wilayah": item.get("wilayah", ""),
                "topik": topik_dokumen(item),
                "aksi": aksi_dokumen(item),
                "skor": float(cosine_dokumen[i]),
                "skor_contoh": float(cosine_contoh[i]),
                "skor_semantik": float(semantik[i]),
                "bm25": float(bm25[i]),
                "rrf": float(skor_rrf[i]),
                "skor_ranking": float(skor_akhir[i]),
                "rank_semantik": int(rank_semantik[i]),
                "rank_bm25": int(rank_bm25[i]),
            })

        return hasil


if __name__ == "__main__":

    mesin = HybridRetriever()

    pertanyaan = input("Pertanyaan: ").strip()

    if pertanyaan:
        for item in mesin.cari(pertanyaan):
            print(
                f"{item['id']} | {item['judul']} | "
                f"Semantik {item['skor_semantik']:.4f} "
                f"(dok {item['skor']:.4f}, "
                f"contoh {item['skor_contoh']:.4f}) | "
                f"BM25 {item['bm25']:.4f} | "
                f"RRF {item['rrf']:.4f}"
            )