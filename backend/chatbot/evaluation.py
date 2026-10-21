import csv
from pathlib import Path
from retrieval import muat_retrieval, cari_dokumen

# list pertanyaan
pertanyaan_uji = [
    "Bagaimana mengurus KTP yang hilang di Surabaya?",
    "Apa syarat mengganti Kartu Keluarga yang rusak?",
    "Bagaimana prosedur pembuatan SKCK secara online?",
    "Apa ketentuan pindah alamat ke rumah kontrakan?",
    "Berapa harga tiket konser minggu depan?",
    "Apa PIN tanda tangan Ketua RT?"
]

model, embeddings, dokumen = muat_retrieval()
hasil_uji = []

for pertanyaan in pertanyaan_uji:
    hasil = cari_dokumen(
        pertanyaan, model, embeddings, dokumen
    )
    skor = hasil[0]["skor"] if hasil else 0

    status = (
        "SUMBER_DITEMUKAN"
        if skor >= 0.70
        else "FALLBACK"
    )

    hasil_uji.append({
        "pertanyaan": pertanyaan,
        "top_score": round(skor, 4),
        "judul_terdekat": hasil[0]["judul"] if hasil else "",
        "lolos_ambang": skor >= 0.70,
        "status": status
    })

# save hasil
output = Path(__file__).parent / "hasil_uji_retrieval.csv"
with open(output, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file, fieldnames=hasil_uji[0].keys()
    )
    writer.writeheader()
    writer.writerows(hasil_uji)

# tampil hasil
for item in hasil_uji:
    print(
        f"{item['pertanyaan']}\n"
        f"Skor: {item['top_score']}\n"
        f"Status: {item['status']}\n"
    )
print("Hasil pengujian disimpan:", output)
