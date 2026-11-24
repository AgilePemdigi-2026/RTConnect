"""Aturan topik/aksi dan guard untuk chatbot runtime.

Modul ini sengaja tidak bergantung pada sentence-transformers/BM25 supaya
bisa dipakai oleh API Flask yang ringan.
"""

import datetime
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
    (r"\bektp\b|\be-ktp\b|\be\s+ktp\b", "ktp"),
    (r"\bkrtu\s+kelurga\b|\bkrtu\s+kluarga\b|\bkrtu\s+keluarga\b|\bkartu\s+kelurga\b|\bkartu\s+kluarga\b", "kk"),
    (r"\bskk\b(?=.*\b(polri|polisi|aplikasi|online|onlinle|daftar|sidik\s*jari)\b)", "skck"),
    (r"\bhilng\b|\bhlang\b|\bselip\b|\bkecopetan\b", "hilang"),
    (r"\bcetk\s+ulng\b|\bcetak\s+ulng\b|\bcetk\s+ulang\b", "cetak ulang"),
    (r"\brobek\b|\brsk\b|\brusuk\b|\bpatah\b|\bpecah\b|\bsobek\b|\bretak\b|\bburam\b|\bpudar\b|\bterkelupas\b", "rusak"),
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
        r"kos sementara|ktp luar kota|penduduk sementara|"
        r"luar daerah|luar kota|tinggal sementara|tempat tinggal sementara|menumpang tempat tinggal sementara",
        q,
    ))
    if is_nonpermanen:
        found.append("nonpermanen")

    if not is_dom_lembaga and not is_nonpermanen and re.search(
        r"kontrakan|rumah sewa|rumah sewaan|pindah alamat|pindah domisili|menumpang tinggal|pindah datang|perpindahan penduduk|\bbaru pindah\b|\bpindah rumah\b",
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

    if re.search(r"\biuran\b", q):
        found.append("iuran")

    if re.search(r"kerja bakti", q):
        found.append("kerja_bakti")

    return found


TOPIK_KATA_KUNCI = {
    # Kata kunci per topik untuk pewarisan konteks sesi. Setiap nilai wajib
    # memicu topiknya sendiri lewat semua_topik() dan sebisa mungkin tidak
    # mengandung kata pemicu aksi lain.
    "ktp": "KTP",
    "kk": "KK kartu keluarga",
    "skck": "SKCK",
    "domisili": "pindah alamat kontrakan",
    "domisili_lembaga": "surat domisili lembaga",
    "nonpermanen": "nonpermanen kos",
    "nib": "NIB usaha rumahan",
    "kecamatan": "surat keterangan kecamatan",
    "kematian": "kematian",
    "iuran": "iuran",
    "kerja_bakti": "kerja bakti",
}

AKSI_KATA_KUNCI = {
    # Kata kunci per aksi untuk pewarisan konteks sesi. Dipakai hanya bila
    # pertanyaan lanjutan tidak membawa aksi sendiri.
    "hilang": "hilang",
    "rusak": "rusak",
    "perubahan": "perubahan nama",
    "perekaman": "perekaman pertama kali",
    "persyaratan": "syarat",
    "prosedur": "prosedur cara",
    "kontrakan": "kontrakan sewa",
    "verifikasi_alamat": "verifikasi tempat tinggal tidak ditempati",
}

POLA_RUJUKAN_KONTEKS = re.compile(
    r"\b(kalau|kalo|itu|tersebut|tadi|sebelumnya|terus|lanjut|selanjutnya|begitu|demikian|jam berapa|mulai jam|pukul berapa|dimana|di mana|titik kumpul|lokasi|bawa apa)\b|nya\b",
    re.IGNORECASE,
)


def rujukan_konteks(query):
    """True jika pertanyaan mengandung rujukan ke pembahasan sebelumnya."""
    return bool(POLA_RUJUKAN_KONTEKS.search(normalisasi(query)))


def konteks_pertanyaan(query, riwayat):
    """Bangun kueri efektif dengan konteks sesi yang sama.

    riwayat: daftar pesan warga tersanitasi sesi ini (terlama -> terbaru),
    tanpa placeholder kredensial. Aturan:
    - Tanpa riwayat: kembalikan query apa adanya (sesi baru tanpa konteks).
    - Query bertopik eksplisit: topik baru menang, riwayat diabaikan.
    - Tanpa penanda rujukan: konteks tidak dipakai.
    - Riwayat tanpa topik: maksud belum jelas, kembalikan query agar
      guardklarifikasi (PERTANYAAN_TIDAK_JELAS / PERLU_VERIFIKASI) bekerja.
    - Aksi riwayat hanya diwariskan bila query tidak membawa aksi sendiri.
    """
    if not riwayat:
        return query
    if semua_topik(query):
        return query
    if not rujukan_konteks(query):
        return query
    kata = []
    for teks in reversed(riwayat):
        topiks = semua_topik(teks)
        if topiks:
            kata.append(TOPIK_KATA_KUNCI.get(topiks[0], topiks[0]))
            break
    if not kata:
        return query
    aksi_query = aksi_pertanyaan(query)
    if not aksi_query or aksi_query in ("persyaratan", "prosedur"):
        # Query lanjutan tanpa aksi spesifik ("Syaratnya apa saja?") atau
        # beraksi generik: wariskan aksi spesifik pembahasan sebelumnya
        # (mis. "hilang") agar dokumen yang tepat yang terangkat.
        for teks in reversed(riwayat):
            previous_topics = semua_topik(teks)
            if previous_topics and previous_topics[0] != topiks[0]:
                break  # Jangan wariskan aksi dari topik yang lebih lama.
            aksi = aksi_pertanyaan(teks)
            if aksi and aksi not in ("persyaratan", "prosedur"):
                kata.append(AKSI_KATA_KUNCI.get(aksi, aksi))
                break
    return f"{query} {' '.join(kata)}"


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
        r"tanpa benar-benar tinggal|tidak saya tempati|alamat yang tidak ditempati|"
        r"tidak benar-benar tinggal|menolak perpindahan",
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

    if re.search(r"pertama kali|usia 17|umur 17|perekaman|rekam|belum (pernah )?(punya|memiliki|bikin|buat)", q):
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
        (
            re.search(r"\b(rt|ketua rt)\b", q)
            and re.search(
                r"surat|pengantar|iuran|kas|balai|kerja bakti|"
                r"tanda tangan|sku|domisili",
                q,
            )
        )
        or re.search(r"kerja bakti", q)
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


def mask_pii(teks: str) -> str:
    """Masking data identitas pribadi (NIK 16 digit dan Nomor Telepon Indonesia) dengan mempertahankan delimiter."""
    t = str(teks)

    # 1. Mask NIK 16 digit (kontinu, bertanda hubung, atau berspasi)
    def _rep_nik(m):
        p1, sep1, p2, sep2, p3, sep3, p4 = m.groups()
        s1 = sep1 if sep1 else ''
        s2 = sep2 if sep2 else ''
        s3 = sep3 if sep3 else ''
        return f'{p1}{s1}****{s2}****{s3}{p4}'

    pola_nik = re.compile(r'\b(\d{4})([-\s]?)(\d{4})([-\s]?)(\d{4})([-\s]?)(\d{4})\b')
    t = pola_nik.sub(_rep_nik, t)

    # 2. Mask Nomor Telepon Indonesia (10-13 digit diawali +62, 62, atau 08 dengan variasi pemisah)
    pola_phone = re.compile(
        r'(?:\+?62[-\s]?|0)8[0-9]{1,3}(?:[-\s]?[0-9]{3,4}){2,3}\b'
    )

    def _rep_phone(m):
        raw = m.group(0)
        digits = re.sub(r'\D', '', raw)
        total_digits = len(digits)
        if total_digits < 10 or total_digits > 13:
            return raw

        if raw.startswith('+62'):
            prefix_digits = 5
        elif raw.startswith('62'):
            prefix_digits = 5
        else:
            prefix_digits = 4

        suffix_digits = 4

        digit_count = 0
        masked_chars = []
        for ch in raw:
            if ch.isdigit():
                digit_count += 1
                if digit_count <= prefix_digits or digit_count > (total_digits - suffix_digits):
                    masked_chars.append(ch)
                else:
                    masked_chars.append('*')
            else:
                masked_chars.append(ch)
        return ''.join(masked_chars)

    t = pola_phone.sub(_rep_phone, t)
    return t


POLA_SSH_PEM = re.compile(
    r'-----BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY-----',
    re.IGNORECASE,
)

POLA_SEED_INDICATOR = re.compile(
    r'\b(?:seed\s+phrase|recovery\s+phrase|mnemonic(?:\s+phrase)?|frasa\s+pemulihan|kunci\s+pemulihan)\b',
    re.IGNORECASE,
)


SENTENCE_FUNCTION_WORDS = {
    # Indonesian sentence words
    'dan', 'atau', 'yang', 'agar', 'supaya', 'untuk', 'dengan', 'pada', 'di', 'ke',
    'dari', 'tetap', 'setiap', 'hari', 'bagaimana', 'cara', 'menjaga', 'keamanan',
    'adalah', 'yaitu', 'bisa', 'dapat', 'harus', 'tidak', 'boleh', 'apakah', 'kenapa',
    'mengapa', 'saya', 'kamu', 'anda', 'mereka', 'kita', 'dalam', 'ini', 'itu',
    # Verba/adjektiva naratif pengantar — tidak mungkin menjadi bagian payload
    # seed-phrase acak ('catat' tindakan menulis; 'aman'/'darurat'/'keadaan'
    # konteks naratif; 'simpan'/'tulis'/'pegang' tindakan menyimpan/menitip).
    # Kata benda domain (dompet/digital/kripto/wallet/dll) TETAP dikecualikan karena
    # dapat muncul sah di dalam frasa kepemilikan pengantar ("untuk dompet saya"):
    # memasukkannya menyebabkan pengantar payload yang sah ikut dihitung sebagai
    # kalimat natural (false negative).
    'catat', 'mencatat', 'simpan', 'menyimpan', 'tulis', 'menulis', 'pegang',
    'aman', 'darurat', 'keadaan',
    # Kosa kata naratif dan edukasi keamanan/administrasi umum
    'panduan', 'pemula', 'membahas', 'risiko', 'pencurian', 'aset',
    'melalui', 'aplikasi', 'palsu', 'perangkat', 'rusak', 'kebocoran',
    'bocor', 'serta', 'praktik', 'pemulihan', 'tentang', 'terhadap',
    # English sentence words (function words, question words, verbs)
    'and', 'how', 'people', 'should', 'protect', 'their', 'when', 'using', 'hardware',
    'wallets', 'wallet', 'what', 'why', 'where', 'explain', 'tell', 'safe', 'keep',
    'store', 'offline', 'online', 'secure', 'security', 'does', 'mean', 'difference',
    'between', 'public', 'private', 'keys', 'phrase', 'words',
    # Kata kerja/kata benda umum yang menandakan kalimat naratif/edukatif,
    # bukan daftar kata acak seed phrase.
    'jaga', 'lindungi', 'cadangan', 'mencadangkan',
    'protecting', 'keeping', 'keeping',
}


def contains_raw_ssh_or_seed_phrase(text: str) -> bool:
    """Deteksi kredensial sensitif mentah (SSH Private Key PEM/OpenSSH & Seed/Recovery Phrase aktual).

    Mendukung pemisah spasi, koma, tanda hubung, dan penomoran list.
    Menghindari false positive pada kalimat tanya/edukatif bahasa Indonesia dan bahasa Inggris.

    Aturan umum (bukan hardcode kalimat contoh):
    1. Pindai SETIAP kemunculan indikator seed phrase dalam teks (bukan hanya yang pertama).
    2. Setelah indikator, lewati connector pengantar generik (tanda baca, kata kerja bantu,
       frasa "untuk dompet saya", "dompet digital saya", dst.) — pengantar semacam ini
       adalah pola umum frasa kepemilikan, bukan bukti kalimat edukatif.
    3. Geser jendela 12 kata di seluruh token alfabet setelah indikator dan nilai
       SETIAP rentang 12 kata berurutan sebagai kandidat payload — pengantar
       naratif ("saya catat dengan aman untuk keadaan darurat") boleh mendahului
       payload; yang dinilai adalah struktur payload itu sendiri, bukan posisi awal.
    4. Tolak kandidat hanya jika mengandung >=2 kata fungsi/kalimat yang TIDAK mungkin
       menjadi bagian payload acak (kata sambung, kata tanya, verba naratif).
       Kata benda domain ("dompet", "digital", "kripto") TIDAK dihitung karena
       dapat muncul sah di dalam konteks pengantar payload.
    5. Jika salah satu indikator menghasilkan payload valid 12 kata, kembalikan True.
    """
    if POLA_SSH_PEM.search(text):
        return True

    for m in POLA_SEED_INDICATOR.finditer(text):
        after = text[m.end():]

        # Bersihkan connector pengantar payload (misal: ':', '=', '-', 'adalah', 'yaitu', 'saya', 'untuk dompet digital saya', dsb.)
        # Pola domain dibuat umum (dompet + opsional digital + opsional saya, dst.)
        # agar varian kepemilikan apa pun terbuang sebelum jendela 12 kata dievaluasi.
        cleaned_after = re.sub(
            r'^(?:[\s:=_\-,]|adalah|yaitu|saya|milik(?:\s+saya)?|untuk(?:\s+(?:dompet(?:\s+digital)?|wallet|akun|digital|kripto|crypto)(?:\s+saya)?)?|dompet(?:\s+digital)?(?:\s+saya)?|wallet(?:\s+saya)?|akun(?:\s+saya)?|digital(?:\s+saya)?|kripto(?:\s+saya)?|crypto(?:\s+saya)?|berikut|ini|cadangan(?:\s+untuk)?)+',
            ' ',
            after,
            flags=re.IGNORECASE,
        ).strip()

        cleaned_words = re.sub(r'\b\d+[\.:\s]+', ' ', cleaned_after)
        tokens = re.split(r'[\s,;\.\:\?!/\\(\)\[\]"\']+', cleaned_words.strip())
        words = [w.lower() for w in tokens if re.fullmatch(r'[a-zA-Z]{3,12}', w)]

        # Jendela geser: nilai setiap rentang 12 kata berurutan. Pengantar
        # naratif sebelum payload ("saya catat dengan aman untuk ...") tidak
        # boleh mencemari penilaian — yang dinilai struktur payload itu sendiri.
        for start in range(0, max(len(words) - 11, 1)):
            candidate = words[start:start + 12]
            if len(candidate) < 12:
                break
            sentence_word_count = sum(1 for w in candidate if w in SENTENCE_FUNCTION_WORDS)
            if sentence_word_count >= 2:
                continue
            return True

        # shortcut: tidak ada rentang 12 kata bersih; lanjut ke indikator berikut.

    return False


def is_sensitive_credential_for_storage(query_text: str) -> bool:
    """Pemeriksaan sanitasi pre-persistence terpisah dari intent classification RAG.

    Menentukan apakah pesan pengguna mengandung kredensial rahasia (PIN, password, token,
    kunci SSH, atau seed phrase) yang wajib disamarkan sebelum disimpan ke database.
    """
    if cek_keamanan(query_text) == 'RAHASIA':
        return True
    if contains_raw_ssh_or_seed_phrase(query_text):
        return True
    return False


POLA_RAHASIA = re.compile(
    r'\b(pin|otp|password|pass|passwd|kata sandi|kode rahasia|token|api key|apikey|secret key|secret|bearer\s+[a-z0-9\-_.]+|jwt\s+[a-z0-9\-_.]+|eyjhbgcioi[a-z0-9\-_.]*|sk-[a-z0-9_-]{8,})\b'
)

POLA_INJEKSI = re.compile(
    r'abaikan (semua )?(instruksi|aturan)|lupakan (semua )?(instruksi|aturan)|ignore (all |previous )*instructions|system prompt|prompt sistem'
)

# Objek kredensial dan kata kerja permintaan bocor/minta spesifik
_ROBJ = r'(?:pin|otp|password|pass|passwd|kata\s*sandi|kode\s*rahasia|token|api\s*key|apikey|secret\s*key|secret|bearer|jwt)'
_VERB_EKSPLOIT = r'(?:bocorkan|bocorin|ungkapkan|tunjukkan|buka|lihat|ketikkan|tampilkan|kirim|kirimkan|bagi|bagikan|kasih|spill|sebutkan|minta|mendapatkan|dapatkan|memperoleh|peroleh|mengakses|akses|mengambil|ambil|ambilkan|mencuri|curi|tahu|mengetahui|berikan)'
_TARGET_MILIK = r'(?:rt|ketua\s*rt|bendahara\s*rt|bendahara|admin|database|mysql|sistem|aplikasi|kamu|anda|pengurus|warga|orang\s*lain)'

_P_MINTA_EKSPLISIT = rf'\b{_VERB_EKSPLOIT}\b.*?\b{_ROBJ}\b'
_P_TANYA_NILAI = rf'\b(?:apa|berapa|mana)\s+(?:kode\s+)?{_ROBJ}\b'
_P_MILIK_SPESIFIK = rf'\b{_ROBJ}\s+(?:milik|punya|dari)?\s*{_TARGET_MILIK}\b'
_P_ROOT = rf'\b(?:root\s+password|kode\s+rahasia\s+rt|pin\s+rahasia)\b'

# 1. Definisi atau konsep umum
POLA_DEFINISI = re.compile(
    rf'\b(?:apa\s+(?:itu|artinya|arti|maksud\s+dari|definisi)|jelaskan\s+(?:apa\s+itu|tentang|konsep))\s+{_ROBJ}\b'
)

# 2. Contoh kredensial / rekomendasi pembuatan kredensial baru yang kuat
POLA_CONTOH_BUAT = re.compile(
    rf'\b(?:(?:contoh|rekomendasi)\s+{_ROBJ}|'
    r'(?:membuat|bikin|generate|menyusun|membuatkan)\s+.*?' + _ROBJ + r'.*?(?:kuat|panjang|aman|baru)|'
    r'(?:tunjukkan|berikan|kasih|lihat)\s+contoh\s+' + _ROBJ + r')\b'
)

# 3. Best practice / tata cara pengelolaan akun / aturan / keamanan / login / verifikasi
POLA_BEST_PRACTICE = re.compile(
    rf'\b(?:(?:perlu|harus|wajib|bolehkah|apakah|mengapa|kenapa)\b.*?\b{_ROBJ}\b|'
    rf'\b{_ROBJ}\b.*?\b(?:diganti|diubah|dirahasiakan|disimpan|diberikan|disebarkan|pengesahan|keamanan|kuat|disarankan|reset)\b|'
    r'\b(?:panjang|kombinasi|karakter)\s+' + _ROBJ + r'|'
    r'\b(?:amankah|keamanan\s+akun|mengamankan\s+akun|lupa\s+' + _ROBJ + r')\b|'
    r'\b(?:cara|bagaimana|tips|panduan|langkah|aturan)\s+.*?(?:menjaga|mengamankan|merahasiakan|keamanan|membuat|bikin|reset)\b)'
)


def cek_keamanan(pertanyaan):
    """Periksa apakah pertanyaan mengandung permintaan informasi rahasia atau injeksi prompt."""
    if contains_raw_ssh_or_seed_phrase(pertanyaan):
        return "RAHASIA"

    sec_q = normalisasi_keamanan(pertanyaan)
    has_injection = bool(POLA_INJEKSI.search(sec_q))
    has_rahasia = bool(POLA_RAHASIA.search(sec_q))

    # 1. Kueri tanpa kata kunci kredensial
    if not has_rahasia:
        if has_injection:
            return "LUAR_CAKUPAN"
        return None

    # 2. Injeksi prompt bersama kata kredensial mutlak diblokir
    if has_injection:
        return "RAHASIA"

    is_eksploit = False

    for m in re.finditer(_P_MINTA_EKSPLISIT, sec_q):
        sub = m.group(0)
        # Jika sub-frase yang cocok adalah 'berikan tips', 'tunjukkan contoh', dsb -> abaikan
        if re.search(r'^\w+\s+(?:tips|panduan|contoh|rekomendasi)\b', sub):
            continue
        is_eksploit = True
        break

    if not is_eksploit and re.search(rf'({_P_TANYA_NILAI}|{_P_ROOT})', sec_q):
        if not POLA_DEFINISI.search(sec_q):
            is_eksploit = True

    if not is_eksploit and re.search(_P_MILIK_SPESIFIK, sec_q):
        has_ask_verb = bool(re.search(rf'\b({_VERB_EKSPLOIT}|apa\s+{_ROBJ}|berapa\s+{_ROBJ})\b', sec_q))
        if re.search(r'\b(menjaga|mengamankan)\s+keamanan\b', sec_q) and not has_ask_verb:
            pass
        elif re.search(r'\b(apakah|mengapa|kenapa)\s+.*?(wajib|perlu|harus|memerlukan)\b', sec_q) and not has_ask_verb:
            pass
        elif re.search(r'\b(lupa\s+' + _ROBJ + r'|reset)\b', sec_q) and not has_ask_verb:
            pass
        else:
            is_eksploit = True

    if is_eksploit:
        return "RAHASIA"

    # Jika dalam konteks definisi, contoh aman, atau best practice, loloskan
    if POLA_DEFINISI.search(sec_q) or POLA_CONTOH_BUAT.search(sec_q) or POLA_BEST_PRACTICE.search(sec_q):
        return None

    # Default aman jika menyebut kata kredensial tanpa konteks penjelasan yang jelas
    return "RAHASIA"


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


def klarifikasi_layanan_umum(pertanyaan: str) -> dict | str | None:
    """Deteksi pertanyaan umum mengenai layanan yang memiliki banyak cabang prosedur
    atau membutuhkan konfirmasi data mutakhir pengurus RT.

    Mengembalikan dict berisi answer, citation, status, dan is_escalated bila ada informasi spesifik,
    atau str berisi pertanyaan klarifikasi terarah, atau None bila kueri spesifik.
    """
    q = normalisasi(pertanyaan).strip()
    topiks = semua_topik(q)
    aksi = aksi_pertanyaan(q)

    # 1. Kasus KTP tanpa aksi spesifik
    if "ktp" in topiks and aksi in (None, "persyaratan", "prosedur"):
        if not re.search(
            r"hilang|rusak|patah|pecah|sobek|usia 17|umur 17|rekam|pertama kali|belum (pernah )?(punya|memiliki|bikin)|ganti nama|ubah|pindah",
            q,
        ):
            return (
                "Untuk pengurusan KTP di Surabaya, layanannya terbagi berdasarkan keperluan: "
                "1. Perekaman baru (usia 17 tahun), "
                "2. Penggantian KTP hilang, "
                "3. Penggantian KTP rusak, atau "
                "4. Perubahan data/alamat. Keperluan mana yang ingin Anda urus?"
            )

    # 2. Kasus KK tanpa aksi spesifik
    if "kk" in topiks and aksi in (None, "persyaratan", "prosedur"):
        if not re.search(
            r"hilang|rusak|sobek|patah|pecah|ubah|ganti nama|koreksi|tambah anggota",
            q,
        ):
            return (
                "Untuk layanan Kartu Keluarga (KK), keperluannya dibedakan menjadi: "
                "1. Penggantian KK rusak, "
                "2. Penggantian KK hilang, atau "
                "3. Perubahan elemen data KK. Layanan mana yang Anda butuhkan?"
            )

    # 3. Kasus Pindah Domisili Umum di Surabaya (RTC-019 kontrakan vs RTC-020 verifikasi alamat)
    # Jika sumber tidak cukup, langsung sediakan eskalasi WhatsApp dengan draf pertanyaan warga
    if "domisili" in topiks and re.search(r"pindah", q):
        if not re.search(r"kontrakan|sewa|sewaan|pemilik rumah|sptjm|fiktif|tidak tinggal|tidak ditempati|verifikasi tempat tinggal", q):
            return {
                'answer': (
                    "Informasi umum kepindahan domisili belum sepenuhnya tersedia pada basis pengetahuan RTConnect. "
                    "Dokumen resmi yang tercatat saat ini mencakup pindah datang ke rumah kontrakan dan verifikasi alamat tempat tinggal. "
                    "Silakan konfirmasi prosedur kepindahan domisili Anda kepada pengurus RT melalui tombol WhatsApp di bawah."
                ),
                'status': 'KLARIFIKASI_DIBUTUHKAN',
                'is_escalated': True,
                'citation': None,
            }

    # Kasus baru pindah tanpa aksi spesifik
    if "domisili" in topiks and re.search(r"\b(baru pindah|baru datang|pindah ke sini)\b", q):
        if not re.search(r"kontrakan|sewa|kos|surat pindah|sptjm|verifikasi", q):
            return {
                'answer': (
                    "Selamat datang di lingkungan RT 04 / RW 09 Gunungsari Indah. "
                    "Untuk pelaporan warga baru pindah dan pengurusan surat domisili, "
                    "silakan konfirmasi langsung kepada pengurus RT melalui tombol WhatsApp di bawah."
                ),
                'status': 'KLARIFIKASI_DIBUTUHKAN',
                'is_escalated': True,
                'citation': None,
            }

    # 4. Kasus Surat Domisili Usaha / SKU
    # Jelaskan layanan SKU yang tersedia di RTConnect, bedakan NIB OSS dan Kelurahan, sediakan eskalasi
    if re.search(r"\b(domisili (?:untuk )?usaha|surat domisili (?:untuk )?usaha|surat usaha|sku|keterangan usaha)\b", q):
        return {
            'answer': (
                "Di RTConnect tersedia layanan Surat Keterangan Usaha (SKU) tingkat RT untuk warga yang memiliki tempat usaha fisik. "
                "Untuk perizinan resmi nasional (NIB) diterbitkan melalui portal OSS, sedangkan Surat Domisili Lembaga diterbitkan di kantor kelurahan. "
                "Jika Anda memerlukan surat pengantar khusus lainnya, silakan konfirmasi kepada pengurus RT melalui tombol WhatsApp di bawah."
            ),
            'status': 'KLARIFIKASI_DIBUTUHKAN',
            'is_escalated': True,
            'citation': None,
        }

    return None


def build_escalation_summary(
    query: str,
    query_efektif: str | None = None,
    history: list | None = None,
    ref_date: datetime.date | None = None,
) -> str:
    """Susun ringkasan pertanyaan warga yang setia pada maksud dan bebas PII/kredensial.

    Format ringkasan digunakan sebagai isi draf pesan WhatsApp eskalasi ke Ketua RT (SRS REQ-6).
    """
    # 1. Cek keamanan: jika mengandung data rahasia / kredensial
    if is_sensitive_credential_for_storage(query) or (
        query_efektif and is_sensitive_credential_for_storage(query_efektif)
    ):
        return "Pertanyaan seputar layanan administrasi warga."

    # 2. Sanitasi data sensitif: bersihkan NIK, nomor HP, dan digit sensitif
    q_clean = query.strip()
    q_clean = re.sub(r'\b(nik|no hp|nomor hp|hp|telepon)\s*(?:saya)?\s*[:=]?\s*[0-9*+\-\s]{8,25}\b', '', q_clean, flags=re.IGNORECASE)
    q_clean = re.sub(r'\b[0-9*+\-]{10,20}\b', '', q_clean)
    q_clean = re.sub(r'^\s*(?:dan|lalu|serta)\s+', '', q_clean, flags=re.IGNORECASE)
    q_clean = re.sub(r'\s{2,}', ' ', q_clean).strip(' ,;:-')

    q_norm = normalisasi(q_clean)
    eff_norm = normalisasi(mask_pii(query_efektif or query))

    # 3. Deteksi topik aktif dari riwayat sesi jika pertanyaan pendek/lanjutan
    hist_topic = None
    if history:
        for h in reversed(history):
            h_norm = normalisasi(str(h))
            if 'kerja bakti' in h_norm:
                hist_topic = 'kerja_bakti'
                break
            if 'iuran' in h_norm:
                hist_topic = 'iuran'
                break
            if 'skck' in h_norm:
                hist_topic = 'skck'
                break
            if 'sku' in h_norm or 'usaha' in h_norm:
                hist_topic = 'sku'
                break
            if 'domisili' in h_norm:
                hist_topic = 'domisili'
                break

    # 4. Pertanyaan lanjutan pendek tentang jam / waktu pelaksanaan
    if re.search(r'^(?:mulai\s+)?(?:jam|pukul)\s+berapa\??$', q_norm) or (
        len(q_norm.split()) <= 4 and re.search(r'\b(jam berapa|pukul berapa)\b', q_norm) and 'kerja bakti' not in q_norm
    ):
        if hist_topic == 'kerja_bakti' or 'kerja bakti' in eff_norm:
            return 'Saya ingin menanyakan jam mulai kerja bakti.'
        if hist_topic == 'iuran' or 'iuran' in eff_norm:
            return 'Saya ingin menanyakan jadwal pembayaran iuran lingkungan.'

    # 5. Pertanyaan lanjutan pendek tentang titik kumpul / lokasi
    if re.search(r'^(?:kumpul\s+di\s+mana|titik\s+kumpulnya\s+di\s+mana|lokasinya\s+di\s+mana)\??$', q_norm) or (
        len(q_norm.split()) <= 4 and re.search(r'\b(titik kumpul|kumpul di mana|lokasi kumpul)\b', q_norm) and 'kerja bakti' not in q_norm
    ):
        if hist_topic == 'kerja_bakti' or 'kerja bakti' in eff_norm:
            return 'Saya ingin menanyakan titik kumpul pelaksanaan kerja bakti.'

    # 6. Jika pembersihan PII menyisakan fragmen pendek seperti 'mau tanya iuran'
    if q_norm in ('mau tanya iuran', 'tanya iuran', 'tentang iuran'):
        return 'Saya ingin menanyakan informasi iuran lingkungan RT.'

    # 7. Utamakan pertanyaan asli warga yang telah disanitasi:
    # Mempertahankan semua maksud (biaya dan waktu, jam dan lokasi, konfirmasi bayar, dll.)
    res = re.sub(r'[\r\n]+', ' ', q_clean).strip()
    if not res:
        return 'Pertanyaan seputar layanan administrasi warga.'
    res = res[0].upper() + res[1:]
    if not res.endswith('?'):
        res = res.rstrip('.') + '.'

    # Pertahankan pertanyaan warga; tambahkan konteks untuk rujukan seperti
    # 'syaratnya' / 'caranya', tanpa menyalin riwayat atau data pribadi.
    if not semua_topik(query) and rujukan_konteks(query):
        effective = query_efektif or konteks_pertanyaan(query, history or [])
        topics = semua_topik(effective)
        if len(topics) == 1:
            topic = topics[0]
            label = {'ktp': 'KTP', 'kk': 'Kartu Keluarga', 'skck': 'SKCK',
                     'nib': 'NIB'}.get(topic, topic.replace('_', ' '))
            action = aksi_pertanyaan(effective)
            # Ungkapkan konteks sebagai kalimat warga, bukan metadata teknis.
            # Jangan mengklaim kepemilikan dokumen atau menambah syarat layanan.
            if topic in ('ktp', 'kk', 'skck', 'nib'):
                if action in ('hilang', 'rusak'):
                    context = f'penggantian {label} yang {action}'
                elif action == 'perubahan':
                    context = f'perubahan data pada {label}'
                elif action == 'perekaman' and topic == 'ktp':
                    context = 'perekaman KTP pertama kali'
                else:
                    context = label
                prefix = f'Untuk mengurus {context}'
            else:
                prefix = f'Terkait {label}'
            # Pertahankan seluruh pertanyaan, termasuk biaya DAN waktu, dll.
            res = f'{prefix}, {res[0].lower() + res[1:]}'
    return res
