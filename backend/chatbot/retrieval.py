import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from preprocessing import baca_dataset, pilih_referensi

folder_cache = Path(__file__).parent / "cache"

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
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    return model, embeddings, dokumen

# search dokumen berdasarkan pertanyaan
def cari_dokumen(pertanyaan, model, embeddings, dokumen, top_k=3):
    vektor = model.encode(
        [pertanyaan],
        normalize_embeddings=True
    )[0]

    skor = embeddings @ vektor
    indeks = np.argsort(skor)[::-1][:top_k]
    hasil = []

    for i in indeks:
        item = dokumen[i]
        hasil.append({
            "id": item["id"],
            "judul": item["judul"],
            "konten": item["konten"],
            "sumber": item.get("url_sumber", ""),
            "skor": float(skor[i])
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
            print(f"Similarity: {item['skor']:.4f}")
            print(f"Sumber: {item['sumber']}")

        if hasil and hasil[0]["skor"] >= 0.70:
            print("\nSumber ditemukan")
        else:
            print("\nInformasi belum ditemukan")
    else:
        print("Pertanyaan tidak boleh kosong")
