import re


STOP = {
    "yang", "di", "dan", "ini", "itu", "ke",
    "dari", "untuk", "pada", "dengan", "adalah",
    "bisa", "dapat", "saya", "apa", "bagaimana",
    "berapa", "kapan", "apakah", "ingin", "mau",
    "tolong", "rt", "ketua",
    # kata tanya umum yang tidak membawa topik
    "lama", "masa", "mana", "sampai", "saja",
    "harus", "boleh",
}

# Topik spesifik mengalahkan topik umum (ktp/kk).
TOPIK_SPESIFIK = [
    ("skck", r"\bskck\b"),
    ("nib", r"\bnib\b|izin berusaha|usaha rumahan"),
    (
        "domisili_lembaga",
        None  # dicek khusus di bawah
    ),
    (
        "nonpermanen",
        r"nonpermanen|non permanen|\bkos\b|"
        r"ktp luar kota|penduduk sementara"
    ),
    (
        "domisili",
        r"kontrakan|rumah sewa|pindah alamat|"
        r"menumpang tinggal|pindah datang"
    ),
    ("kematian", r"kematian"),
    (
        "kecamatan",
        None  # dicek khusus di bawah
    ),
]

TOPIK_UMUM = [
    ("kk", r"\bkk\b"),
    ("ktp", r"\bktp\b|perekaman identitas"),
]

# Kata yang menandakan pertanyaan administrasi
# yang belum ada di knowledge base.
ADMIN_LAIN = (
    r"\bakta\b|\bkia\b|paspor|bpjs|\bsim\b|stnk|bpkb|"
    r"npwp|pinjol|pinjaman online|disalahgunakan|"
    r"dipakai orang|penipuan"
)

# Kelompok kata "penentu": jika ditanyakan tetapi tidak ada di
# dokumen, dokumen tidak boleh dipakai sebagai jawaban pasti.
KELOMPOK_PENENTU = {
    "biaya", "tarif", "gratis", "denda",
    "bayar", "membayar", "dipungut",
}


def normalisasi(teks):
    teks = str(teks).lower()

    padanan = [
        ("retak", "rusak"),
        ("kesalahan nama", "perubahan nama"),
        ("pindah tempat tinggal", "pindah alamat"),
        ("pindah domisili", "pindah alamat"),
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


def tokenisasi_bm25(teks):
    """Token untuk BM25: kata umum dibuang."""
    return [k for k in tokenisasi(teks) if k not in STOP]


def semua_topik(teks):
    """Daftar topik yang terdeteksi.

    Topik spesifik didahulukan. Jika hanya topik umum (ktp, kk),
    semuanya dikembalikan agar pertanyaan multi-topik terdeteksi.
    """
    q = normalisasi(teks)
    spesifik = []

    for nama, pola in TOPIK_SPESIFIK:
        if nama == "domisili_lembaga":
            cocok = "domisili" in q and "lembaga" in q
        elif nama == "kecamatan":
            cocok = "surat keterangan" in q and "kecamatan" in q
        else:
            cocok = bool(re.search(pola, q))

        if cocok:
            spesifik.append(nama)

    if spesifik:
        return spesifik

    return [
        nama for nama, pola in TOPIK_UMUM
        if re.search(pola, q)
    ]


def topik_pertanyaan(teks):
    topik = semua_topik(teks)
    return topik[0] if topik else None


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
        r"syarat|persyaratan|berkas|dokumen untuk|"
        r"dokumen yang diperlukan",
        q
    ):
        return "persyaratan"

    if re.search(r"prosedur|cara|daftar|online|internet", q):
        return "prosedur"

    return None


def topik_dokumen(item):
    return item.get("entitas_topik") or None


def aksi_dokumen(item):
    return item.get("aksi_topik") or None


def jenis_pertanyaan(teks):
    q = normalisasi(teks)

    if re.search(
        r"\b(pin|otp|password|kata sandi|"
        r"kode rahasia|token akses|api key)\b",
        q
    ):
        return "RAHASIA"

    if re.search(
        r"abaikan (semua )?(instruksi|aturan)|"
        r"lupakan (semua )?(instruksi|aturan)|"
        r"ignore (all |previous )*instructions|"
        r"system prompt|prompt sistem",
        q
    ):
        return "LUAR_CAKUPAN"

    if re.search(
        r"\b(puisi|pantun|lagu|cerpen|resep)\b",
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
        r"kerja bakti|\biuran\b|kas rt|\bronda\b|"
        r"jadwal sampah|balai warga|posyandu rt",
        q
    ):
        return "LOKAL_RT"

    # Administrasi, tetapi belum ada di knowledge base
    if re.search(ADMIN_LAIN, q):
        return "ADMIN_LAIN"

    if semua_topik(q):
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

    def ada(k):
        # cocok persis, atau bentuk berimbuhan (ambil ~ diambil)
        return k in tersedia or (
            len(k) >= 4
            and any(
                len(t) >= 4 and (k in t or t in k)
                for t in tersedia
            )
        )

    return sum(ada(k) for k in kata) / len(kata)


def penentu_hilang(pertanyaan, dokumen):
    """True jika pertanyaan menanyakan biaya/tarif/denda tetapi
    dokumen tidak membahasnya sama sekali."""
    tanya = set(tokenisasi(pertanyaan)) & KELOMPOK_PENENTU

    if not tanya:
        return False

    return not (set(tokenisasi(dokumen)) & KELOMPOK_PENENTU)