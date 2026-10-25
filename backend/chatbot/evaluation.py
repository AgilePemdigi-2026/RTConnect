
import csv
from pathlib import Path

try:
    from .chatbot_service import TanyaRTService
    from .rules import coverage
except ImportError:
    from chatbot_service import TanyaRTService
    from rules import coverage


PERTANYAAN_UJI = [
    ("KTP saya retak, bagaimana mengurus penggantinya?", "ktp"),
    ("Kalau e-KTP rusak, harus mengurus ke mana?", "ktp"),
    ("Bagaimana memperbaiki kesalahan nama pada KK?", "kk"),
    ("KK saya hilang, apakah bisa dicetak lagi?", "kk"),
    ("Bagaimana mengurus SKCK lewat internet?", "skck"),
    ("Apa saja dokumen untuk membuat SKCK?", "skck"),
    ("Saya baru berusia 17 tahun, bagaimana membuat KTP?", "ktp"),
    ("Bagaimana mengurus pindah tempat tinggal?", "domisili"),
    ("Apa yang harus dilakukan penduduk yang tinggal sementara?", "nonpermanen"),
    ("Bagaimana membuat NIB untuk usaha kecil?", "nib"),
    ("Apakah biaya surat pengantar RT sebesar 20 ribu?", "BELUM_ADA_SOP_RT"),
    ("Kapan jadwal kerja bakti di lingkungan RT?", "BELUM_ADA_SOP_RT"),
    ("Berapa PIN untuk menyetujui surat digital?", "RAHASIA"),
    ("Bisakah saya mengetahui password Ketua RT?", "RAHASIA"),
    ("Siapa pemenang pertandingan sepak bola tadi malam?", "LUAR_CAKUPAN"),
    ("Berapa harga tiket bioskop hari ini?", "LUAR_CAKUPAN"),
]


def jalankan_evaluasi():
    layanan = TanyaRTService()
    hasil_uji = []

    for pertanyaan, harapan in PERTANYAAN_UJI:
        respons = layanan.jawab(pertanyaan)

        dokumen = (
            layanan.retriever.cari(pertanyaan, top_k=3)
            if harapan not in {
                "BELUM_ADA_SOP_RT",
                "RAHASIA",
                "LUAR_CAKUPAN"
            }
            else []
        )

        terbaik = dokumen[0] if dokumen else None

        cakupan = (
            coverage(
                pertanyaan,
                terbaik["judul"] + " " + terbaik["konten"]
            )
            if terbaik else 0
        )

        hasil_uji.append({
            "pertanyaan": pertanyaan,
            "harapan": harapan,
            "status": respons["status"],
            "top1_id": terbaik["id"] if terbaik else "",
            "top1_judul": terbaik["judul"] if terbaik else "",
            "cosine": round(terbaik["skor"], 4) if terbaik else "",
            "bm25": round(terbaik["bm25"], 4) if terbaik else "",
            "rrf": round(terbaik["rrf"], 5) if terbaik else "",
            "coverage": round(cakupan, 4),
            "relevan_manual": "",
        })

    output = Path(__file__).parent / "hasil_uji_v6.csv"

    with output.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=hasil_uji[0].keys()
        )
        writer.writeheader()
        writer.writerows(hasil_uji)

    print("\nHASIL PENGUJIAN TRAINING V6\n")

    for item in hasil_uji:
        print("Pertanyaan:", item["pertanyaan"])
        print("Status:", item["status"])
        print("Dokumen:", item["top1_judul"])
        print("Cosine:", item["cosine"])
        print("Coverage:", item["coverage"])
        print("-" * 50)

    print("\nHasil disimpan:", output)


if __name__ == "__main__":
    jalankan_evaluasi()
