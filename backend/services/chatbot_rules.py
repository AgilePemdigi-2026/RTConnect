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
}

# Untuk pertanyaan SOP RT, jawaban hanya boleh diambil dari knowledge base
# lokal. Cek cakupan kata mencegah jawaban asal comot hanya karena frasa umum
# "surat pengantar RT" muncul di banyak dokumen.
MIN_LOCAL_RT_BASE = 0.45
MIN_LOCAL_COVERAGE = 0.85

COVERAGE_IGNORE = {
    "yang", "di", "dan", "ini", "itu", "ke", "dari", "untuk", "pada",
    "dengan", "adalah", "sebagai", "dalam", "bisa", "dapat", "oleh",
    "ada", "akan", "atau", "saya", "kami", "kita", "mereka", "dia",
    "apakah", "bagaimana", "apa", "siapa", "berapa", "kapan", "dimana",
    "kenapa", "mengapa", "mana", "mau", "ingin", "mohon", "tolong",
    "masa", "sampai",
}


def normalisasi(teks):
    """Samakan istilah umum sebelum aturan topik/aksi dijalankan."""
    teks = str(teks).lower()
    teks = teks.replace("kartu keluarga", "kk")
    teks = teks.replace("kartu tanda penduduk", "ktp")
    teks = teks.replace("ktp-el", "ktp")
    teks = teks.replace("e-ktp", "ktp")
    teks = teks.replace("nomor induk berusaha", "nib")
    return teks


def tokenisasi(teks):
    return re.findall(r"[a-z0-9]+", normalisasi(teks))


def topik_pertanyaan(teks):
    """Kembalikan topik utama pertanyaan atau None."""
    q = normalisasi(teks)

    if re.search(r"\bskck\b", q):
        return "skck"

    if re.search(r"\bnib\b|izin berusaha|usaha rumahan", q):
        return "nib"

    if "domisili" in q and "lembaga" in q:
        return "domisili_lembaga"

    if re.search(
        r"nonpermanen|non permanen|ngekos|\bkos\b|anak kos|rumah kos|"
        r"kos sementara|ktp luar kota|penduduk sementara",
        q,
    ):
        return "nonpermanen"

    if re.search(
        r"kontrakan|rumah sewa|rumah sewaan|pindah alamat|menumpang tinggal",
        q,
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
    """Kembalikan jenis keperluan pertanyaan atau None."""
    q = normalisasi(teks)

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
    q = normalisasi(pertanyaan)

    if re.search(r"\b(pin|otp|password|kata sandi|kode rahasia)\b", q):
        return "RAHASIA"

    if re.search(r"abaikan instruksi|ignore previous|system prompt|prompt sistem", q):
        return "LUAR_CAKUPAN"

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
