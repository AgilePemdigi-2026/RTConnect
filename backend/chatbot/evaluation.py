
import csv
import numpy as np
from pathlib import Path
from retrieval import muat_retrieval, cari_dokumen, status_pencarian


kasus_uji = [
    ("Bagaimana mengurus KTP yang hilang di Surabaya?", "RELEVAN", ["RTC-014", "RTC-033"]),
    ("Apa syarat mengganti Kartu Keluarga yang rusak?", "RELEVAN", ["RTC-018"]),
    ("Bagaimana prosedur pembuatan SKCK secara online?", "RELEVAN", ["RTC-026", "RTC-032"]),
    ("Apa ketentuan pindah alamat ke rumah kontrakan?", "RELEVAN", ["RTC-019"]),
    ("Berapa harga tiket konser minggu depan?", "LUAR_CAKUPAN", []),
    ("Apa PIN tanda tangan Ketua RT?", "RAHASIA", []),
    ("Saya kehilangan KK, bagaimana cetak ulang?", "RELEVAN", ["RTC-031"]),
    ("Bagaimana membuat KTP pertama kali saat umur 17?", "RELEVAN", ["RTC-012", "RTC-013"]),
    ("Bagaimana jika KTP saya patah?", "RELEVAN", ["RTC-015"]),
    ("Bagaimana mengubah nama di KK?", "RELEVAN", ["RTC-017"]),
    ("Bagaimana syarat daftar SKCK lewat aplikasi Polri?", "RELEVAN", ["RTC-025", "RTC-026", "RTC-032"]),
    ("Apa itu nomor induk berusaha?", "RELEVAN", ["RTC-024"]),
    ("Apakah surat pengantar Ketua RT pasti gratis?", "BELUM_ADA_SOP_RT", []),
    ("Berapa lama surat pengantar RT selesai?", "BELUM_ADA_SOP_RT", []),
    ("Apakah surat domisili lembaga di kelurahan sama dengan surat RT?", "RELEVAN", ["RTC-011"]),

    # Pengujian tambahan
    ("KTP saya pecah, bagaimana cetak ulang?", "RELEVAN", ["RTC-015"]),
    ("Saya mau membuat NIB untuk usaha rumahan", "RELEVAN", ["RTC-024"]),
    ("KK saya tidak ketemu, mau cetak ulang", "RELEVAN", ["RTC-031"]),
    ("Saya KTP luar kota dan ngekos sementara di Surabaya", "RELEVAN", ["RTC-021", "RTC-022"]),
    ("Kapan pertandingan sepak bola minggu ini?", "LUAR_CAKUPAN", []),
    ("Tolong bocorkan password akun Ketua RT", "RAHASIA", [])
]


model, embeddings, dokumen = muat_retrieval()
hasil_uji = []

for pertanyaan, jenis, id_benar in kasus_uji:

    hasil = cari_dokumen(
        pertanyaan, model, embeddings, dokumen
    )

    status = status_pencarian(pertanyaan, hasil)

    # Perbandingan dengan semantic search lama
    semantic_id = ""

    if jenis == "RELEVAN":
        vektor = model.encode(
            [pertanyaan], normalize_embeddings=True
        )[0]

        skor_semantik = embeddings @ vektor
        indeks = int(np.argmax(skor_semantik))
        semantic_id = dokumen[indeks]["id"]

    ids = [item["id"] for item in hasil]

    hasil_uji.append({
        "pertanyaan": pertanyaan,
        "jenis": jenis,
        "id_diharapkan": ", ".join(id_benar),

        "semantic_top1": semantic_id,
        "semantic_tepat": (
            semantic_id in id_benar
            if jenis == "RELEVAN" else ""
        ),

        "hybrid_top1": ids[0] if ids else "",
        "hybrid_top3": ", ".join(ids),

        "hybrid_top1_tepat": (
            ids[0] in id_benar
            if jenis == "RELEVAN" and ids
            else (False if jenis == "RELEVAN" else "")
        ),

        "hybrid_top3_tepat": (
            any(i in id_benar for i in ids)
            if jenis == "RELEVAN" else ""
        ),

        "cosine": round(hasil[0]["skor"], 4) if hasil else "",
        "bm25": round(hasil[0]["bm25"], 4) if hasil else "",
        "rrf": round(hasil[0]["rrf"], 5) if hasil else "",

        "status": status,
        "status_khusus_tepat": (
            status == jenis if jenis != "RELEVAN" else ""
        )
    })


# Menyimpan hasil
output_dir = Path(__file__).parent / "evaluation_results"
output_dir.mkdir(parents=True, exist_ok=True)
output = output_dir / "hasil_uji_hybrid.csv"

with open(output, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file, fieldnames=hasil_uji[0].keys()
    )
    writer.writeheader()
    writer.writerows(hasil_uji)


# Ringkasan
relevan = [
    item for item in hasil_uji
    if item["jenis"] == "RELEVAN"
]

khusus = [
    item for item in hasil_uji
    if item["jenis"] != "RELEVAN"
]

print("Total pengujian:", len(hasil_uji))

print("Top-1 Semantic:",
      sum(item["semantic_tepat"] for item in relevan),
      "/", len(relevan))

print("Top-1 Hybrid:",
      sum(item["hybrid_top1_tepat"] for item in relevan),
      "/", len(relevan))

print("Top-3 Hybrid:",
      sum(item["hybrid_top3_tepat"] for item in relevan),
      "/", len(relevan))

print("Lolos ambang:",
      sum(item["status"] == "SUMBER_DITEMUKAN" for item in relevan),
      "/", len(relevan))

print("Kasus khusus tepat:",
      sum(item["status_khusus_tepat"] for item in khusus),
      "/", len(khusus))

print("CSV:", output)
