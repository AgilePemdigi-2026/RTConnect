"""Aturan topik/aksi dan guard untuk chatbot runtime.

Modul ini sengaja tidak bergantung pada sentence-transformers/BM25 supaya
bisa dipakai oleh API Flask yang ringan.
"""

import re


TOPIK_ID = {
    "ktp": {"RTC-012", "RTC-013", "RTC-014", "RTC-015", "RTC-016", "RTC-033"},
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
    "kontrakan": {"RTC-019"},
    "verifikasi_alamat": {"RTC-020"},
}

# Untuk pertanyaan SOP RT, jawaban hanya boleh diambil dari knowledge base
# lokal. Cek cakupan kata mencegah jawaban asal comot hanya karena frasa umum
# "surat pengantar RT" muncul di banyak dokumen.
MIN_LOCAL_RT_BASE = 0.45
MIN_LOCAL_COVERAGE = 0.80

COVERAGE_IGNORE = {
    "yang", "di", "dan", "ini", "itu", "ke", "dari", "untuk", "pada",
    "dengan", "adalah", "sebagai", "dalam", "bisa", "dapat", "oleh",
    "ada", "akan", "atau", "saya", "kami", "kita", "mereka", "dia",
    "apakah", "bagaimana", "apa", "siapa", "berapa", "kapan", "dimana",
    "kenapa", "mengapa", "mana", "mau", "ingin", "mohon", "tolong",
    "masa", "sampai", "lama",
}


KAMUS_PADANAN_UMUM = [
    # Slang ganti orang / tanya
    (r"\bgue\b|\bgw\b|\baku\b", "saya"),
    (r"\bkudu\b|\bmesti\b", "harus"),
    (r"\bgimana\b|\bbgmana\b|\bbgmna\b", "bagaimana"),
    (r"\bbikin\b|\bbuat\b", "membuat"),
    (r"\bngurus\b", "mengurus"),
    (r"\bbenerin(nya)?\b|\bmembetulkan\b", "perubahan nama"),
    (r"\bselip\b|\bkecopetan\b|\bhilng\b|\bhlang\b", "hilang"),
    (r"\brobek\b|\brsk\b|\brusuk\b|\bpatah\b|\bpecah\b|\bsobek\b|\bretak\b", "rusak"),
    (r"\bonlen\b|\bonlinle\b", "online"),
    (r"\bkluarga\b|\bkelurga\b", "keluarga"),
    (r"\bulng(ny)?\b|\bcetk\b", "cetak ulang"),
    (r"\bpndah\b", "pindah"),
    (r"\brmah\b", "rumah"),
    (r"\bkontrkan\b", "kontrakan"),
    (r"\bsurbya\b|\bsby\b", "surabaya"),
    (r"\bsyrat(ny)?\b|\bsyrt\b", "syarat"),
    (r"\bperekamn\b|\brekaman\b", "perekaman"),
    (r"\bdaftr\b|\bpndaftran\b", "daftar"),
    (r"\bprosdur\b|\balr\b", "prosedur"),
    (r"\bkcamatan\b", "kecamatan"),
    (r"\bngekos\b|\bkosan\b|\bnyewa kos\b|\brantau\b", "nonpermanen"),
    (r"\bjualan cilok\b|\bjualan\b|\busaha kecil\b|\busaha mikro\b", "usaha rumahan"),
]


def normalisasi(teks):
    """Samakan istilah umum sebelum aturan topik/aksi dijalankan."""
    teks = str(teks).lower()
    for pola, pengganti in KAMUS_PADANAN_UMUM:
        teks = re.sub(pola, pengganti, teks)
    teks = teks.replace("kartu keluarga", "kk")
    teks = teks.replace("kartu tanda penduduk", "ktp")
    teks = teks.replace("ktp-el", "ktp")
    teks = teks.replace("e-ktp", "ktp")
    teks = teks.replace("nomor induk berusaha", "nib")
    return teks


def tokenisasi(teks):
    return re.findall(r"[a-z0-9]+", normalisasi(teks))


def semua_topik(teks):
    """Kembalikan semua topik administrasi independen yang terdeteksi dalam teks."""
    q = normalisasi(teks)
    found = []

    if re.search(r"\bskck\b", q):
        found.append("skck")

    if re.search(r"\bnib\b|izin berusaha|usaha rumahan", q):
        found.append("nib")

    is_dom_lembaga = "domisili" in q and "lembaga" in q
    if is_dom_lembaga:
        found.append("domisili_lembaga")

    is_nonpermanen = bool(re.search(
        r"nonpermanen|non permanen|ngekos|\bkos\b|anak kos|rumah kos|"
        r"kos sementara|ktp luar kota|penduduk sementara",
        q,
    ))
    if is_nonpermanen:
        found.append("nonpermanen")

    if not is_dom_lembaga and re.search(
        r"kontrakan|rumah sewa|rumah sewaan|pindah alamat|pindah domisili|menumpang tinggal|pindah datang",
        q,
    ):
        found.append("domisili")

    if re.search(r"\bkk\b", q):
        found.append("kk")

    # Jangan mendeteksi topik KTP jika kueri membahas 'ktp luar kota' yang merupakan konteks nonpermanen
    q_ktp = re.sub(r"ktp luar kota|ktp daerah lain", "", q)
    if re.search(r"\bktp\b|perekaman identitas", q_ktp):
        found.append("ktp")

    if "kematian" in q:
        found.append("kematian")

    if "surat keterangan" in q and "kecamatan" in q:
        found.append("kecamatan")

    return found


def topik_pertanyaan(teks):
    """Kembalikan topik utama pertanyaan atau None."""
    topik_list = semua_topik(teks)
    return topik_list[0] if topik_list else None


def aksi_pertanyaan(teks):
    """Kembalikan jenis keperluan pertanyaan atau None."""
    q = normalisasi(teks)

    # 1. Aksi spesifik domain terlebih dahulu
    if re.search(r"kontrakan|sewa|sewaan|pemilik rumah|sptjm", q):
        return "kontrakan"

    if re.search(
        r"tidak tinggal|tidak ditempati|fiktif|verifikasi tempat tinggal|"
        r"tanpa benar-benar tinggal|tidak saya tempati",
        q,
    ):
        return "verifikasi_alamat"

    if re.search(r"hilang|kehilangan|tidak ketemu", q):
        return "hilang"

    if re.search(r"rusak|sobek|patah|pecah|tidak terbaca", q):
        return "rusak"

    if re.search(
        r"ubah|perubahan|mengoreksi|koreksi|salah nama|ganti nama|perbaiki nama",
        q,
    ):
        return "perubahan"

    if re.search(r"pertama kali|usia 17|umur 17|perekaman|rekam", q):
        return "perekaman"

    if re.search(r"syarat|persyaratan|berkas", q):
        return "persyaratan"

    if re.search(r"prosedur|cara|daftar|online", q):
        return "prosedur"

    return None


def topik_dokumen(kode_sumber):
    if not kode_sumber:
        return None
    for topik, ids in TOPIK_ID.items():
        if kode_sumber in ids:
            return topik
    return None


def aksi_dokumen(kode_sumber):
    if not kode_sumber:
        return None
    for aksi, ids in AKSI_ID.items():
        if kode_sumber in ids:
            return aksi
    return None


def is_rt_surat_question(pertanyaan):
    """True untuk pertanyaan SOP surat/pengantar tingkat RT."""
    q = normalisasi(pertanyaan)
    return bool(
        re.search(r"\b(rt|ketua rt)\b", q)
        and re.search(r"surat|pengantar", q)
        and not (
            "domisili" in q
            and "lembaga" in q
            and "kelurahan" in q
        )
    )


def is_local_context_question(pertanyaan):
    """True jika pertanyaan membahas konteks yang dimiliki KB lokal RT."""
    q = normalisasi(pertanyaan)
    return bool(
        re.search(r"\b(rt|ketua rt)\b", q)
        and re.search(
            r"surat|pengantar|iuran|kas|balai|kerja bakti|"
            r"tanda tangan|sku|domisili",
            q,
        )
    )


def coverage_score(pertanyaan, teks):
    """Rasio kata pertanyaan yang benar-benar muncul di teks kandidat."""
    q_tokens = [
        token for token in tokenisasi(pertanyaan)
        if len(token) > 1 and token not in COVERAGE_IGNORE
    ]
    if not q_tokens:
        return 0.0

    text_tokens = set(tokenisasi(teks))
    matched = 0
    for token in q_tokens:
        if any(
            token == candidate
            or (len(token) >= 3 and token in candidate)
            or (len(candidate) >= 3 and candidate in token)
            for candidate in text_tokens
        ):
            matched += 1
    return matched / len(q_tokens)


def normalisasi_keamanan(teks):
    """Normalisasi khusus untuk deteksi keamanan (leetspeak, spasi/tanda hubung antar-karakter).
    
    Tidak digunakan untuk tokenisasi retrieval agar tidak merusak pencarian teks dokumen.
    """
    t = str(teks).lower()
    # Hapus tanda hubung/titik/garis bawah di antara karakter tunggal: p-i-n -> pin
    t = re.sub(r'(?<=\b[a-z0-9])[.\-_](?=[a-z0-9]\b|[a-z0-9][.\-_])', '', t)
    # Hapus spasi di antara karakter tunggal: p i n -> pin
    t = re.sub(r'(?<=\b[a-z0-9])\s+(?=[a-z0-9]\b|[a-z0-9]\s)', '', t)
    # Normalisasi leetspeak umum
    leet = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '@': 'a',
        '$': 's',
        '5': 's',
    }
    return ''.join([leet.get(c, c) for c in t])


POLA_RAHASIA = re.compile(
    r'\b(pin|otp|password|pass|passwd|kata sandi|kode rahasia|token|api key|apikey|secret key|secret)\b'
)

POLA_INJEKSI = re.compile(
    r'abaikan (semua )?(instruksi|aturan)|lupakan (semua )?(instruksi|aturan)|ignore (all |previous )*instructions|system prompt|prompt sistem'
)

POLA_EDUKATIF_KEAMANAN = re.compile(
    r'\b(tips|panduan|cara menjaga|bagaimana menjaga|menjaga keamanan|mengamankan|keamanan akun|amankah)\b'
)

POLA_MINTA_KREDENSIAL = re.compile(
    r'\b(apa|berapa|mana|berikan|bocorkan|minta|lihat|ketikkan|tampilkan|kirim|bagi)\b'
)


def cek_keamanan(pertanyaan):
    """Periksa apakah pertanyaan mengandung permintaan informasi rahasia atau injeksi prompt."""
    sec_q = normalisasi_keamanan(pertanyaan)
    if POLA_RAHASIA.search(sec_q):
        # Bedakan pertanyaan edukatif/keamanan akun dengan permintaan membocorkan kredensial
        if POLA_EDUKATIF_KEAMANAN.search(sec_q) and not POLA_MINTA_KREDENSIAL.search(sec_q):
            return None
        return "RAHASIA"
    if POLA_INJEKSI.search(sec_q):
        return "LUAR_CAKUPAN"
    return None


POLA_TIDAK_JELAS = re.compile(
    r'^(syarat(nya)?\s*(apa|gimana)?(\s*aja)?(\s*ya)?|berapa lama proses(nya)?(\s*sampai selesai)?|tolong bantu saya( mengurus ini)?|bantu saya|tolong bantu)$'
)

POLA_AMBIGU_VERIFIKASI = re.compile(
    r'(perpanjang surat|biaya pengurusan(nya)?|berkas saya sudah lengkap|apakah berkas (saya )?lengkap)'
)

POLA_ADMIN_LAIN = re.compile(
    r'\b(pinjol|pinjaman online|akta kelahiran|akta lahir|kartu identitas anak|\bkia\b|\bsim\b|stnk|bpkb|paspor|bpjs|pajak kendaraan|samsat|buku nikah|\bkua\b|sertifikat tanah|\bbpn\b)\b'
)


def batasan(
    pertanyaan,
    best_score=0.0,
    answer_threshold=0.70,
    best_is_local=False,
    best_base_score=None,
    best_coverage=None,
):
    """Tentukan apakah pertanyaan harus ditolak/dieskalasi sebelum dijawab.

    best_score adalah skor ranking kandidat teratas. best_base_score adalah
    skor lexical mentahnya, dan best_coverage adalah rasio kata pertanyaan yang
    muncul di kandidat lokal. Ketiganya dipakai untuk mencegah jawaban SOP RT
    yang hanya cocok secara frasa umum.
    """
    sec_guard = cek_keamanan(pertanyaan)
    if sec_guard:
        return sec_guard

    q = normalisasi(pertanyaan).strip().rstrip('?').strip()

    # Guard kueri ambigu tanpa subjek layanan spesifik
    if POLA_TIDAK_JELAS.search(q):
        return "PERTANYAAN_TIDAK_JELAS"

    if POLA_AMBIGU_VERIFIKASI.search(q):
        return "PERLU_VERIFIKASI"

    # Pertanyaan mengenai administrasi di luar basis data resmi (pinjol, paspor, sim, dll)
    if POLA_ADMIN_LAIN.search(q):
        return "PERLU_VERIFIKASI"

    topik = topik_pertanyaan(q)

    if topik is not None:
        return None

    # Pertanyaan tentang surat/pengantar RT hanya boleh dijawab jika memang
    # ada sumber lokal yang cukup kuat dan kata-kata penting pertanyaan
    # benar-benar tercakup. Jika tidak, jangan mengarang SOP.
    if is_rt_surat_question(q):
        local_base = (
            best_score if best_base_score is None else best_base_score
        )
        coverage = 1.0 if best_coverage is None else best_coverage
        if (
            best_is_local
            and best_score >= answer_threshold
            and local_base >= MIN_LOCAL_RT_BASE
            and coverage >= MIN_LOCAL_COVERAGE
        ):
            return None
        return "BELUM_ADA_SOP_RT"

    if best_score >= answer_threshold:
        return None

    return "LUAR_CAKUPAN"
