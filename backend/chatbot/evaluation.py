
import csv
import numpy as np
from pathlib import Path
from retrieval import muat_retrieval, cari_dokumen

# Pertanyaan pengujian
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
    ("Apakah surat domisili lembaga di kelurahan sama dengan surat RT?", "RELEVAN", ["RTC-011"])
]

model, embeddings, dokumen = muat_retrieval()
ambang = 0.70
hasil_uji = []

for pertanyaan, jenis, id_benar in kasus_uji:

    # Semantic Search
    vektor = model.encode(
        [pertanyaan], normalize_embeddings=True
    )[0]

    skor_semantik = embeddings @ vektor
    urutan_semantik = np.argsort(-skor_semantik)[:3]
    hasil_semantik = [dokumen[i] for i in urutan_semantik]

    # Hybrid Retrieval
    hasil_hybrid = cari_dokumen(
        pertanyaan, model, embeddings, dokumen, top_k=3
    )

    top_semantik = hasil_semantik[0]
    top_hybrid = hasil_hybrid[0] if hasil_hybrid else None

    relevan = jenis == "RELEVAN"

    top1_semantik = (
        top_semantik["id"] in id_benar
        if relevan else None
    )

    top1_hybrid = (
        bool(top_hybrid and top_hybrid["id"] in id_benar)
        if relevan else None
    )

    top3_hybrid = (
        any(item["id"] in id_benar for item in hasil_hybrid)
        if relevan else None
    )

    skor_hybrid = top_hybrid["skor"] if top_hybrid else 0.0

    hasil_uji.append({
        "pertanyaan": pertanyaan,
        "jenis_uji": jenis,
        "id_diharapkan": ", ".join(id_benar),
        "semantic_top1": top_semantik["id"],
        "semantic_skor": round(float(skor_semantik[urutan_semantik[0]]), 4),
        "semantic_top1_tepat": top1_semantik,
        "hybrid_top1": top_hybrid["id"] if top_hybrid else "",
        "hybrid_judul": top_hybrid["judul"] if top_hybrid else "",
        "hybrid_top3": ", ".join(item["id"] for item in hasil_hybrid),
        "hybrid_cosine": round(float(skor_hybrid), 4),
        "hybrid_bm25": round(top_hybrid["bm25"], 4) if top_hybrid else None,
        "hybrid_rrf": round(top_hybrid["rrf"], 5) if top_hybrid else None,
        "hybrid_top1_tepat": top1_hybrid,
        "hybrid_top3_tepat": top3_hybrid,
        "lolos_ambang": skor_hybrid >= ambang
    })

# Simpan CSV
output = Path(__file__).parent / "hasil_uji_hybrid.csv"

with open(output, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file, fieldnames=hasil_uji[0].keys()
    )
    writer.writeheader()
    writer.writerows(hasil_uji)

# Ringkasan pengujian
data_relevan = [
    item for item in hasil_uji
    if item["jenis_uji"] == "RELEVAN"
]

print("Jumlah pertanyaan:", len(hasil_uji))
print("Pertanyaan relevan:", len(data_relevan))

print("Top-1 Semantic tepat:",
      sum(item["semantic_top1_tepat"] for item in data_relevan),
      "/", len(data_relevan))

print("Top-1 Hybrid tepat:",
      sum(item["hybrid_top1_tepat"] for item in data_relevan),
      "/", len(data_relevan))

print("Top-3 Hybrid tepat:",
      sum(item["hybrid_top3_tepat"] for item in data_relevan),
      "/", len(data_relevan))

print("Pertanyaan relevan lolos ambang:",
      sum(item["lolos_ambang"] for item in data_relevan),
      "/", len(data_relevan))

print("Hasil disimpan:", output)
