
import json
import re
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from preprocessing import baca_dataset, pilih_referensi

folder_cache = Path(__file__).parent / "cache"


def tokenisasi(teks):
    teks = str(teks).lower()
    teks = teks.replace("kartu keluarga", "kk")
    teks = teks.replace("kartu tanda penduduk", "ktp")
    teks = teks.replace("ktp-el", "ktp")
    teks = teks.replace("e-ktp", "ktp")

    return re.findall(r"[a-z0-9]+", teks)


def muat_retrieval():
    data = baca_dataset()
    referensi = pilih_referensi(data)

    embeddings = np.load(folder_cache / "embeddings.npy")

    with open(folder_cache / "ids.json", "r", encoding="utf-8") as file:
        ids = json.load(file)

    data_referensi = {item["id"]: item for item in referensi}

    if len(ids) != len(embeddings):
        raise ValueError("Jumlah embedding dan ID tidak sesuai")

    if len(set(ids)) != len(ids) or set(ids) != set(data_referensi):
        raise ValueError("Dataset berubah, jalankan ulang embedding.py")

    dokumen = [data_referensi[id] for id in ids]

    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    return model, embeddings, dokumen


def cari_dokumen(pertanyaan, model, embeddings, dokumen, top_k=3):

    # Semantic search
    vektor = model.encode(
        [pertanyaan],
        normalize_embeddings=True
    )[0]

    skor_semantik = embeddings @ vektor

    # BM25 keyword search
    korpus = []

    for item in dokumen:
        pertanyaan_contoh = item.get("contoh_pertanyaan") or []
        kata_kunci = item.get("kata_kunci") or []

        teks = " ".join([
            item["judul"],
            item["judul"],
            item["kategori"],
            item["konten"],
            " ".join(pertanyaan_contoh),
            " ".join(kata_kunci)
        ])

        korpus.append(tokenisasi(teks))

    bm25 = BM25Okapi(korpus)
    skor_bm25 = bm25.get_scores(tokenisasi(pertanyaan))

    # Mengurutkan hasil kedua metode
    urutan_semantik = np.argsort(-skor_semantik)
    urutan_bm25 = np.argsort(-skor_bm25)

    # Menggabungkan ranking menggunakan RRF
    skor_rrf = np.zeros(len(dokumen))

    for posisi, indeks in enumerate(urutan_semantik):
        skor_rrf[indeks] += 1 / (60 + posisi + 1)

    if np.max(skor_bm25) > 0:
        for posisi, indeks in enumerate(urutan_bm25):
            skor_rrf[indeks] += 1 / (60 + posisi + 1)

    # Mengambil dokumen dengan ranking terbaik
    urutan_akhir = sorted(
        range(len(dokumen)),
        key=lambda i: (-skor_rrf[i], -skor_semantik[i])
    )[:top_k]

    hasil = []

    for i in urutan_akhir:
        item = dokumen[i]

        hasil.append({
            "id": item["id"],
            "judul": item["judul"],
            "konten": item["konten"],
            "sumber": item.get("url_sumber", ""),
            "skor": float(skor_semantik[i]),
            "bm25": float(skor_bm25[i]),
            "rrf": float(skor_rrf[i])
        })

    return hasil


if __name__ == "__main__":
    model, embeddings, dokumen = muat_retrieval()

    pertanyaan = input("Masukkan pertanyaan: ").strip()

    if pertanyaan:
        hasil = cari_dokumen(
            pertanyaan, model, embeddings, dokumen
        )

        print("\nHasil pencarian:")

        for item in hasil:
            print(f"\n{item['judul']}")
            print(f"Cosine: {item['skor']:.4f}")
            print(f"BM25: {item['bm25']:.4f}")
            print(f"RRF: {item['rrf']:.4f}")
            print(f"Sumber: {item['sumber']}")

        if hasil:
            skor = hasil[0]["skor"]

            if skor >= 0.70:
                print("\nStatus: SUMBER_DITEMUKAN")
            else:
                print("\nStatus: PERLU_VERIFIKASI")
                print("Dokumen terkait ditemukan, tetapi skor belum memenuhi ambang.")
        else:
            print("\nStatus: FALLBACK")
            print("Tidak ada dokumen yang ditemukan.")
    else:
        print("Pertanyaan tidak boleh kosong")
