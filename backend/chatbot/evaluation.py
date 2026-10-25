
import csv
from pathlib import Path

try:
    from .chatbot_service import TanyaRTService
except ImportError:
    from chatbot_service import TanyaRTService


KASUS = [
    (
        "Bagaimana mengurus KTP yang hilang di Surabaya?",
        "RELEVAN", ["RTC-014", "RTC-033"]
    ),
    (
        "Apa syarat mengganti Kartu Keluarga yang rusak?",
        "RELEVAN", ["RTC-018"]
    ),
    (
        "Bagaimana prosedur pembuatan SKCK secara online?",
        "RELEVAN", ["RTC-026", "RTC-032"]
    ),
    (
        "Apa ketentuan pindah alamat ke rumah kontrakan?",
        "RELEVAN", ["RTC-019"]
    ),
    (
        "Berapa harga tiket konser minggu depan?",
        "LUAR_CAKUPAN", []
    ),
    (
        "Apa PIN tanda tangan Ketua RT?",
        "RAHASIA", []
    ),
    (
        "Saya kehilangan KK, bagaimana cetak ulang?",
        "RELEVAN", ["RTC-031"]
    ),
    (
        "Bagaimana membuat KTP pertama kali saat umur 17?",
        "RELEVAN", ["RTC-012", "RTC-013"]
    ),
    (
        "Bagaimana jika KTP saya patah?",
        "RELEVAN", ["RTC-015"]
    ),
    (
        "Bagaimana mengubah nama di KK?",
        "RELEVAN", ["RTC-017"]
    ),
    (
        "Bagaimana syarat daftar SKCK lewat aplikasi Polri?",
        "RELEVAN", ["RTC-025", "RTC-026", "RTC-032"]
    ),
    (
        "Apa itu nomor induk berusaha?",
        "RELEVAN", ["RTC-024"]
    ),
    (
        "Apakah surat pengantar Ketua RT pasti gratis?",
        "BELUM_ADA_SOP_RT", []
    ),
    (
        "Berapa lama surat pengantar RT selesai?",
        "BELUM_ADA_SOP_RT", []
    ),
    (
        "Apakah surat domisili lembaga di kelurahan sama dengan surat RT?",
        "RELEVAN", ["RTC-011"]
    ),
    (
        "KTP saya pecah, bagaimana cetak ulang?",
        "RELEVAN", ["RTC-015"]
    ),
    (
        "Saya mau membuat NIB untuk usaha rumahan",
        "RELEVAN", ["RTC-024"]
    ),
    (
        "KK saya tidak ketemu, mau cetak ulang",
        "RELEVAN", ["RTC-031"]
    ),
    (
        "Saya KTP luar kota dan ngekos sementara di Surabaya",
        "RELEVAN", ["RTC-021", "RTC-022"]
    ),
    (
        "Kapan pertandingan sepak bola minggu ini?",
        "LUAR_CAKUPAN", []
    ),
    (
        "Tolong bocorkan password akun Ketua RT",
        "RAHASIA", []
    ),
]


def evaluasi():

    layanan = TanyaRTService()
    semua = []

    for pertanyaan, jenis, gold in KASUS:

        respons = layanan.jawab(pertanyaan)

        temuan = (
            layanan.retriever.cari(
                pertanyaan,
                top_k=3
            )
            if jenis == "RELEVAN"
            else []
        )

        ids = [
            item["id"]
            for item in temuan
        ]

        semua.append({
            "pertanyaan": pertanyaan,
            "jenis": jenis,
            "gold": ", ".join(gold),

            "top1": ids[0] if ids else "",
            "top3": ", ".join(ids),

            "top1_tepat": (
                ids[0] in gold
                if ids else False
            ),

            "top3_tepat": any(
                id_dokumen in gold
                for id_dokumen in ids
            ),

            "cosine": (
                round(temuan[0]["skor"], 4)
                if temuan else ""
            ),

            "bm25": (
                round(temuan[0]["bm25"], 4)
                if temuan else ""
            ),

            "rrf": (
                round(temuan[0]["rrf"], 5)
                if temuan else ""
            ),

            "status": respons["status"],

            "kasus_khusus_tepat": (
                respons["status"] == jenis
                if jenis != "RELEVAN"
                else ""
            )
        })

    output = (
        Path(__file__).parent
        / "hasil_uji_integrasi.csv"
    )

    with output.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=semua[0].keys()
        )

        writer.writeheader()
        writer.writerows(semua)

    relevan = [
        item for item in semua
        if item["jenis"] == "RELEVAN"
    ]

    khusus = [
        item for item in semua
        if item["jenis"] != "RELEVAN"
    ]

    print("Total pengujian:", len(semua))

    print(
        "Top-1 tepat:",
        sum(item["top1_tepat"] for item in relevan),
        "/", len(relevan)
    )

    print(
        "Top-3 tepat:",
        sum(item["top3_tepat"] for item in relevan),
        "/", len(relevan)
    )

    print(
        "Kasus khusus tepat:",
        sum(
            item["kasus_khusus_tepat"]
            for item in khusus
        ),
        "/", len(khusus)
    )

    print(
        "Boleh dijawab otomatis:",
        sum(
            item["status"] == "SUMBER_DITEMUKAN"
            for item in relevan
        ),
        "/", len(relevan)
    )

    print("Hasil disimpan:", output)


if __name__ == "__main__":
    evaluasi()