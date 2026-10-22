
import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from preprocessing import baca_dataset, pilih_referensi


folder_cache = Path(__file__).parent / "cache"
ambang = 0.70

nama_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Pengelompokan dokumen berdasarkan topik
topik_id = {
    "ktp": {"RTC-012", "RTC-013", "RTC-014", "RTC-015", "RTC-016", "RTC-033"},
    "kk": {"RTC-017", "RTC-018", "RTC-031"},
    "skck": {"RTC-025", "RTC-026", "RTC-032"},
    "domisili": {"RTC-019", "RTC-020"},
    "domisili_lembaga": {"RTC-011"},
    "nonpermanen": {"RTC-021", "RTC-022"},
    "nib": {"RTC-024"},
    "kecamatan": {"RTC-010"},
    "kematian": {"RTC-023"}
}

aksi_id = {
    "hilang": {"RTC-014", "RTC-031", "RTC-033"},
    "rusak": {"RTC-015", "RTC-018"},
    "perubahan": {"RTC-016", "RTC-017"},
    "perekaman": {"RTC-012", "RTC-013"},
    "persyaratan": {"RTC-025"},
    "prosedur": {"RTC-026", "RTC-032"}
}


# Membersihkan dan menyamakan istilah
def normalisasi(teks):
    teks = str(teks).lower()
    teks = teks.replace("kartu keluarga", "kk")
    teks = teks.replace("kartu tanda penduduk", "ktp")
    teks = teks.replace("ktp-el", "ktp")
    teks = teks.replace("e-ktp", "ktp")
    teks = teks.replace("nomor induk berusaha", "nib")
    return teks


def tokenisasi(teks):
    return re.findall(r"[a-z0-9]+", normalisasi(teks))


# Mengenali topik pertanyaan
def topik_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(r"\bskck\b", q):
        return "skck"

    if re.search(r"\bnib\b|izin berusaha|usaha rumahan", q):
        return "nib"

    if "domisili" in q and "lembaga" in q:
        return "domisili_lembaga"

    if re.search(
        r"nonpermanen|non permanen|ngekos|kos sementara|ktp luar kota|penduduk sementara",
        q
    ):
        return "nonpermanen"

    if re.search(
        r"kontrakan|rumah sewa|rumah sewaan|pindah alamat|menumpang tinggal",
        q
    ):
        return "domisili"

    if re.search(r"\bkk\b", q):
        return "kk"

    if re.search(r"\bktp\b|perekaman identitas", q):
        return "ktp"

    if "kematian" in q:
        return "kematian"

    if "surat keterangan" in q and "kecamatan" in q:
        return "kecamatan"

    return None


# Mengenali jenis keperluan
def aksi_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(r"hilang|kehilangan|tidak ketemu", q):
        return "hilang"

    if re.search(r"rusak|sobek|patah|pecah|tidak terbaca", q):
        return "rusak"

    if re.search(
        r"ubah|perubahan|mengoreksi|koreksi|salah nama|ganti nama|perbaiki nama",
        q
    ):
        return "perubahan"

    if re.search(r"pertama kali|usia 17|umur 17|perekaman|rekam", q):
        return "perekaman"

    if re.search(r"syarat|persyaratan|berkas", q):
        return "persyaratan"

    if re.search(r"prosedur|cara|daftar|online", q):
        return "prosedur"

    return None


# Pemeriksaan sebelum pencarian
def batasan(pertanyaan):
    q = normalisasi(pertanyaan)

    if re.search(r"\b(pin|otp|password|kata sandi|kode rahasia)\b", q):
        return "RAHASIA"

    # Belum tersedia SOP lokal RT yang terverifikasi
    if (
        re.search(r"\b(rt|ketua rt)\b", q)
        and re.search(r"surat|pengantar", q)
        and not (
            "domisili" in q
            and "lembaga" in q
            and "kelurahan" in q
        )
    ):
        return "BELUM_ADA_SOP_RT"

    if topik_pertanyaan(q) is None:
        return "LUAR_CAKUPAN"

    return None


# Membaca metadata topik dokumen
def topik_dokumen(item):
    if item.get("entitas_topik"):
        return item["entitas_topik"]

    for topik, ids in topik_id.items():
        if item["id"] in ids:
            return topik

    return None


def aksi_dokumen(item):
    if item.get("aksi_topik"):
        return item["aksi_topik"]

    for aksi, ids in aksi_id.items():
        if item["id"] in ids:
            return aksi

    return None


# Memuat dataset dan embedding
def muat_retrieval():
    data = baca_dataset()
    referensi = pilih_referensi(data)

    embeddings = np.load(folder_cache / "embeddings.npy")

    with open(folder_cache / "ids.json", "r", encoding="utf-8") as file:
        ids = json.load(file)

    data_referensi = {item["id"]: item for item in referensi}

    if (
        len(ids) != len(embeddings)
        or len(set(ids)) != len(ids)
        or set(ids) != set(data_referensi)
    ):
        raise ValueError(
            "Dataset dan embedding tidak cocok. Jalankan embedding.py lagi."
        )

    dokumen = [data_referensi[id] for id in ids]
    model = SentenceTransformer(nama_model)

    return model, embeddings, dokumen


# Hybrid Retrieval

def cari_dokumen(pertanyaan, model, embeddings, dokumen, top_k=3):

    if batasan(pertanyaan):
        return []

    if not dokumen:
        return []

    topik = topik_pertanyaan(pertanyaan)
    aksi = aksi_pertanyaan(pertanyaan)

    # 1. Semantic Search seluruh dokumen
    vektor = model.encode(
        [pertanyaan], normalize_embeddings=True
    )[0]

    skor_semantik = embeddings @ vektor

    # 2. Persiapan BM25 seluruh dokumen
    korpus = []

    for item in dokumen:
        teks = " ".join([
            item["judul"],
            item["judul"],
            item.get("kategori", ""),
            item.get("konten", ""),
            " ".join(item.get("kata_kunci") or []),
            " ".join(item.get("contoh_pertanyaan") or [])
        ])

        korpus.append(tokenisasi(teks))

    bm25 = BM25Okapi(korpus)

    # Menyamakan beberapa istilah untuk pencarian kata
    query_bm25 = normalisasi(pertanyaan)

    padanan = {
        "patah": "rusak",
        "pecah": "rusak",
        "sobek": "rusak",
        "kehilangan": "hilang",
        "tidak ketemu": "hilang",
        "mengubah": "perubahan",
        "ubah": "perubahan",
        "ngekos": "nonpermanen"
    }

    for kata, pengganti in padanan.items():
        query_bm25 = re.sub(
            r"\b" + re.escape(kata) + r"\b",
            pengganti,
            query_bm25
        )

    skor_bm25 = bm25.get_scores(tokenisasi(query_bm25))
    skor_bm25 = np.maximum(skor_bm25, 0)

    # 3. Ranking kedua metode
    ranking_semantik = np.argsort(
        -skor_semantik, kind="stable"
    )

    ranking_bm25 = np.argsort(
        -skor_bm25, kind="stable"
    )

    # 4. Menggabungkan ranking menggunakan RRF
    skor_rrf = np.zeros(len(dokumen))

    for posisi, indeks in enumerate(
        ranking_semantik, start=1
    ):
        skor_rrf[indeks] += 1 / (60 + posisi)

    for posisi, indeks in enumerate(
        ranking_bm25, start=1
    ):
        if skor_bm25[indeks] > 0:
            skor_rrf[indeks] += 1 / (60 + posisi)

    # 5. Penyesuaian relevansi topik dan keperluan
    skor_akhir = skor_rrf.copy()

    for i, item in enumerate(dokumen):

        topik_cocok = (
            topik is not None
            and topik_dokumen(item) == topik
        )

        aksi_cocok = (
            aksi is not None
            and aksi_dokumen(item) == aksi
        )

        if topik_cocok:
            skor_akhir[i] += 0.010

        if topik_cocok and aksi_cocok:
            skor_akhir[i] += 0.004

    # 6. Mengurutkan hasil akhir
    urutan = sorted(
        range(len(dokumen)),
        key=lambda i: (
            -skor_akhir[i],
            -skor_semantik[i]
        )
    )[:top_k]

    hasil = []

    for i in urutan:
        item = dokumen[i]

        hasil.append({
            "id": item["id"],
            "judul": item["judul"],
            "konten": item["konten"],
            "sumber": item.get("url_sumber", ""),
            "skor": float(skor_semantik[i]),
            "bm25": float(skor_bm25[i]),
            "rrf": float(skor_rrf[i]),
            "skor_ranking": float(skor_akhir[i])
        })

    return hasil


# Menentukan status pencarian
def status_pencarian(pertanyaan, hasil):
    blok = batasan(pertanyaan)

    if blok:
        return blok

    if not hasil:
        return "FALLBACK"

    if hasil[0]["skor"] >= ambang:
        return "SUMBER_DITEMUKAN"

    return "PERLU_VERIFIKASI"


if __name__ == "__main__":
    model, embeddings, dokumen = muat_retrieval()

    pertanyaan = input("Pertanyaan: ").strip()

    if pertanyaan:
        hasil = cari_dokumen(
            pertanyaan, model, embeddings, dokumen
        )

        for item in hasil:
            print(f"\n{item['judul']}")
            print(f"Cosine: {item['skor']:.4f}")
            print(f"BM25: {item['bm25']:.4f}")
            print(f"RRF: {item['rrf']:.4f}")
            print(f"Sumber: {item['sumber']}")

        print("\nStatus:", status_pencarian(pertanyaan, hasil))

    else:
        print("Pertanyaan tidak boleh kosong")
