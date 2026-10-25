
import re


TOPIK_ID = {
    "ktp": {
        "RTC-012", "RTC-013", "RTC-014",
        "RTC-015", "RTC-016", "RTC-033"
    },
    "kk": {"RTC-017", "RTC-018", "RTC-031"},
    "skck": {"RTC-025", "RTC-026", "RTC-032"},
    "domisili": {"RTC-019", "RTC-020"},
    "domisili_lembaga": {"RTC-011"},
    "nonpermanen": {"RTC-021", "RTC-022"},
    "nib": {"RTC-024"},
    "kecamatan": {"RTC-010"},
    "kematian": {"RTC-023"},
}

AKSI_ID = {
    "hilang": {"RTC-014", "RTC-031", "RTC-033"},
    "rusak": {"RTC-015", "RTC-018"},
    "perubahan": {"RTC-016", "RTC-017"},
    "perekaman": {"RTC-012", "RTC-013"},
    "persyaratan": {"RTC-025"},
    "prosedur": {"RTC-026", "RTC-032"},
}

STOP = {
    "yang", "di", "dan", "ini", "itu", "ke",
    "dari", "untuk", "pada", "dengan", "adalah",
    "bisa", "dapat", "saya", "apa", "bagaimana",
    "berapa", "kapan", "apakah", "ingin", "mau",
    "tolong", "rt", "ketua"
}


def normalisasi(teks):
    teks = str(teks).lower()

    padanan = [
        ("retak", "rusak"),
        ("kesalahan nama", "perubahan nama"),
        ("pindah tempat tinggal", "pindah alamat"),
        ("tinggal sementara", "nonpermanen"),
        ("dokumen persyaratan", "persyaratan"),
        ("kartu keluarga", "kk"),
        ("kartu tanda penduduk", "ktp"),
        ("ktp-el", "ktp"),
        ("e-ktp", "ktp"),
        ("nomor induk berusaha", "nib"),
        ("tidak ketemu", "hilang"),
        ("kehilangan", "hilang"),
        ("patah", "rusak"),
        ("pecah", "rusak"),
        ("sobek", "rusak"),
        ("mengubah", "perubahan"),
        ("ngekos", "nonpermanen"),
    ]

    for lama, baru in padanan:
        teks = re.sub(
            r"\b" + re.escape(lama) + r"\b",
            baru,
            teks
        )

    return teks


def tokenisasi(teks):
    return re.findall(r"[a-z0-9]+", normalisasi(teks))


def topik_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(r"\bskck\b", q):
        return "skck"

    if re.search(
        r"\bnib\b|izin berusaha|usaha rumahan", q
    ):
        return "nib"

    if "domisili" in q and "lembaga" in q:
        return "domisili_lembaga"

    if re.search(
        r"nonpermanen|non permanen|\bkos\b|"
        r"ktp luar kota|penduduk sementara",
        q
    ):
        return "nonpermanen"

    if re.search(
        r"kontrakan|rumah sewa|pindah alamat|"
        r"menumpang tinggal",
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


def aksi_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(r"\bhilang\b", q):
        return "hilang"

    if re.search(r"rusak|tidak terbaca", q):
        return "rusak"

    if re.search(
        r"perubahan|ubah|mengoreksi|koreksi|"
        r"salah nama|ganti nama",
        q
    ):
        return "perubahan"

    if re.search(
        r"pertama kali|usia 17|umur 17|perekaman|rekam",
        q
    ):
        return "perekaman"

    if re.search(
        r"syarat|persyaratan|berkas|dokumen untuk|dokumen yang diperlukan",
        q
    ):
        return "persyaratan"

    if re.search(r"prosedur|cara|daftar|online", q):
        return "prosedur"

    return None


def topik_dokumen(item):
    if item.get("entitas_topik"):
        return item["entitas_topik"]

    for nama, ids in TOPIK_ID.items():
        if item["id"] in ids:
            return nama

    return None


def aksi_dokumen(item):
    if item.get("aksi_topik"):
        return item["aksi_topik"]

    for nama, ids in AKSI_ID.items():
        if item["id"] in ids:
            return nama

    return None


def jenis_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(
        r"\b(pin|otp|password|kata sandi|"
        r"kode rahasia|token akses|api key)\b",
        q
    ):
        return "RAHASIA"

    if re.search(
        r"abaikan instruksi|ignore previous|"
        r"system prompt|prompt sistem",
        q
    ):
        return "LUAR_CAKUPAN"

    # Pertanyaan tentang pelayanan internal RT
    if (
        re.search(r"\b(rt|ketua rt)\b", q)
        and re.search(
            r"surat|pengantar|iuran|kas|kerja bakti|"
            r"balai|posyandu|jadwal|layanan|domisili|"
            r"tanda tangan|biaya|gratis",
            q
        )
        and not (
            "domisili" in q
            and "lembaga" in q
            and "kelurahan" in q
        )
    ):
        return "LOKAL_RT"

    if re.search(
        r"kerja bakti|iuran warga|kas rt|"
        r"jadwal sampah|balai warga|posyandu rt",
        q
    ):
        return "LOKAL_RT"

    if topik_pertanyaan(q) is not None:
        return "PEMERINTAH"

    return "LUAR_CAKUPAN"


def coverage(pertanyaan, dokumen):
    kata = {
        k for k in tokenisasi(pertanyaan)
        if len(k) > 1 and k not in STOP
    }

    if not kata:
        return 0.0

    tersedia = set(tokenisasi(dokumen))

    return len(kata & tersedia) / len(kata)
