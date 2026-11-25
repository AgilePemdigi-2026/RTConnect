"""Guardrail asisten AI pengisi surat (masukan asisten praktikum & dosen).

AI dipakai sebagai *drafter* (pengusul isian), bukan pembuat keputusan. Lima risiko
penggunaan AI sebagai drafter dokumen ditangani di sini, SEMUANYA di sisi server
(deterministik, tidak bergantung pada kepatuhan model):

1. Sesuai SOP         -> check_sop(): jenis surat hanya dari daftar aktif, tujuan surat
                         harus instansi yang sah untuk jenis itu (mis. SKCK -> kepolisian),
                         satu pengajuan = satu jenis surat, AI tidak pernah mengisi
                         identitas (nama/NIK/KK/agama/alamat) dan tidak menyetujui surat.
2. Akurat menangkap intent -> detect_intent(): intent & keyakinan dari AI dicocokkan
                         dengan kata kunci di cerita warga. Ambigu / yakin rendah ->
                         bertanya balik, bukan menebak. Di luar layanan -> diarahkan.
3. Mengikuti template -> to_template_value(): AI hanya mengisi kolom; isi surat dibuat
                         dari template resmi. Nilai dibersihkan jadi satu baris pendek
                         tanpa markdown / penanda template / tautan.
4. Tahan prompt injection -> sanitize_story() membuang instruksi sisipan sebelum dikirim,
                         cerita dibungkus pembatas acak sebagai DATA, keluaran AI yang
                         berbau instruksi ditolak, dan kolom keluaran dibatasi whitelist.
5. Tidak mengarang    -> ground_field(): setiap nilai harus punya bukti di cerita warga
                         (kutipan ditemukan di cerita). Nilai tanpa bukti dibuang dan
                         ditandai "Perlu diisi"; AI boleh menjawab tidak tahu (null).
"""
import re
import secrets

from services.letter_guidance import sop_for, wilayah_words

# ----------------------------------------------------------- 4. prompt injection

INJECTION_PATTERNS = [
    r'abaikan\s+(semua\s+|seluruh\s+)?(aturan|instruksi|perintah|prompt)',
    r'lupakan\s+(semua\s+|seluruh\s+)?(aturan|instruksi|perintah|prompt)',
    r'(ubah|ganti|timpa)\s+(aturan|instruksi|sistem|prompt)',
    r'ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above)?\s*(instructions?|rules?|prompts?)',
    r'disregard\s+(all\s+|the\s+)?(previous|above|prior)',
    r'(system|developer)\s*prompt',
    r'prompt\s+sistem',
    r'kamu\s+(sekarang\s+)?(adalah|menjadi)\s+(admin|sistem|developer|ketua\s+rt|ai\s+lain)',
    r'kamu\s+sekarang\s+(adalah\s+|menjadi\s+)?\w+',
    r'you\s+are\s+now',
    r'\bact\s+as\b',
    r'berperan(lah)?\s+sebagai',
    r'jailbreak|\bDAN\s+mode\b|mode\s+developer|developer\s+mode',
    r'(setujui|sahkan|tanda\s*tangani|approve)\s+(surat|pengajuan)\s+(ini|saya)?\s*(otomatis|langsung|sekarang)',
    r'(tampilkan|bocorkan|sebutkan|print|reveal)\s+.{0,20}(prompt|instruksi|aturan)',
    r'</?\s*(system|assistant|user|instruction|cerita_warga)[^>]*>',
    r'\[\s*/?\s*(INST|SYS|system)\s*\]',
    r'```',
    r'"""',
    r'\{\{.*?\}\}',
    r'jawab(lah)?\s+(dengan|hanya)\s+json',
    r'(isi|set|tulis)\s+(kolom\s+)?"?(nik|nama|status|jenis_surat_kode|nomor_kk)"?\s*(=|:|dengan|menjadi)',
]
_INJECTION_RE = re.compile('|'.join(f'(?:{p})' for p in INJECTION_PATTERNS), re.IGNORECASE)

# Keluaran AI yang tidak pantas masuk ke kolom surat
_OUTPUT_BAD_RE = re.compile(
    r'https?://|www\.|<[^>]+>|\{\{|\}\}|```|\bjson\b|\bprompt\b|\binstruksi\b|\bsystem\b'
    r'|abaikan|ignore|sebagai\s+ai|saya\s+adalah\s+ai|as\s+an\s+ai',
    re.IGNORECASE)


def sanitize_story(text: str):
    """Buang instruksi sisipan dari cerita warga. Mengembalikan (cerita_bersih, terdeteksi)."""
    found = bool(_INJECTION_RE.search(text or ''))
    clean = _INJECTION_RE.sub(' [bagian dihapus] ', text or '')
    # Karakter pembatas tidak boleh dipakai warga untuk "menutup" blok cerita
    clean = clean.replace('<', ' ').replace('>', ' ')
    clean = re.sub(r'[ \t]+', ' ', clean).strip()
    return clean, found


def new_delimiter() -> str:
    """Pembatas acak per permintaan: penyerang tidak bisa menebak tag penutupnya."""
    return f'cerita_warga_{secrets.token_hex(4)}'


def looks_like_instruction(value: str) -> bool:
    return bool(value) and bool(_OUTPUT_BAD_RE.search(value) or _INJECTION_RE.search(value))


# ----------------------------------------------------------- 3. template

def to_template_value(value, max_len=150):
    """Nilai untuk disisipkan ke template resmi: satu baris, tanpa markdown/penanda template."""
    if not isinstance(value, str):
        return None
    value = re.sub(r'[\r\n\t]+', ' ', value)
    value = re.sub(r'[*_#`|~^\\]+', '', value)          # markdown
    value = re.sub(r'\{\{.*?\}\}', ' ', value)          # penanda template {{ }} dibuang utuh
    value = value.replace('{', '').replace('}', '')
    value = re.sub(r'\s{2,}', ' ', value).strip(' "\'.;:-')
    if not value or value.lower() in {'null', 'none', '-', 'tidak tahu', 'tidak diketahui', 'n/a'}:
        return None
    if len(value) > max_len:  # dipotong di batas kata, bukan di tengah kata
        value = value[:max_len].rsplit(' ', 1)[0]
    return value[0].upper() + value[1:]


# ----------------------------------------------------------- 5. grounding

STOPWORDS = {
    'yang', 'untuk', 'buat', 'bagi', 'di', 'ke', 'dari', 'dan', 'atau', 'saya', 'aku', 'mau', 'ingin',
    'akan', 'ini', 'itu', 'dengan', 'pada', 'sebagai', 'surat', 'pengantar', 'keterangan', 'persyaratan',
    'syarat', 'keperluan', 'pengurusan', 'mengurus', 'urus', 'bikin', 'membuat', 'minta', 'meminta',
    'tolong', 'rt', 'rw', 'nya', 'kak', 'pak', 'bu', 'the', 'adalah', 'juga', 'sudah', 'belum',
    'administrasi', 'pengajuan', 'mengajukan', 'ajukan', 'perlu', 'butuh', 'membutuhkan',
}
# Kata baku/jenis badan yang boleh ditambahkan AI walau tidak diketik warga
EXEMPT_PROPER = {'pt', 'cv', 'tbk', 'ud', 'ktp', 'ktp-el', 'el', 'kk', 'skck', 'rt', 'rw', 'kantor',
                 'kota', 'kabupaten', 'dinas', 'bank', 'persero', 'kelurahan', 'kecamatan', 'polsek',
                 'polrestabes', 'surat', 'persyaratan', 'pengurusan', 'pendaftaran', 'perpanjangan'}


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^0-9a-z\- ]+', ' ', (text or '').lower())).strip()


def _words(text):
    return [w for w in re.split(r'[\s\-]+', normalize(text)) if w]


def _word_in_story(word, story_words):
    for w in story_words:
        if w == word:
            return True
        # imbuhan Bahasa Indonesia: "kerja" ~ "pekerjaan", "daftar" ~ "pendaftaran"
        if len(word) >= 4 and len(w) >= 4 and (word in w or w in word):
            return True
    return False


def _proper_tokens(value):
    """Kata berhuruf kapital (nama perusahaan/sekolah/instansi) & angka, selain kata pertama."""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']*", value)
    return [t for i, t in enumerate(tokens)
            if (t[0].isupper() and i > 0) or t[0].isdigit()]


def _find_quote(story, words):
    """Potongan cerita yang memuat kata-kata bukti (untuk ditampilkan ke warga)."""
    low = story.lower()
    positions = [low.find(w) for w in words if low.find(w) != -1]
    if not positions:
        return None
    start = max(0, min(positions) - 20)
    end = min(len(story), max(positions) + 40)
    quote = ('…' if start else '') + story[start:end].strip() + ('…' if end < len(story) else '')
    quote = re.sub(r'Pesan \d+( \(terbaru\))?:\s*', '', quote)  # label percakapan lanjutan
    return re.sub(r'\s*\n\s*', ' / ', quote)


def _text_grounded(value, story, extra_exempt=()):
    """Teks bebas (keperluan/pekerjaan/tujuan): minimal satu kata isi ada di cerita, dan SEMUA
    nama diri/angka ada di cerita (mencegah AI menambah nama perusahaan/tahun karangan)."""
    story_words = _words(story)
    exempt = EXEMPT_PROPER | set(extra_exempt)
    content = [w for w in _words(value) if len(w) >= 3 and w not in STOPWORDS]
    matched = [w for w in content if _word_in_story(w, story_words)]
    if content and not matched:
        return False, None
    for token in _proper_tokens(value):
        for part in _words(token):
            if part in exempt or len(part) < 2:
                continue
            if not _word_in_story(part, story_words):
                return False, None
    return True, _find_quote(story, matched or content)


JENIS_KELAMIN_KATA = {'Laki-laki': ['laki', 'pria', 'cowok', 'cowo'],
                      'Perempuan': ['perempuan', 'wanita', 'cewek', 'cewe']}
STATUS_KAWIN_KATA = {'Belum Kawin': ['belum kawin', 'belum menikah', 'lajang', 'single', 'bujang'],
                     'Kawin': ['sudah menikah', 'sudah kawin', 'menikah', 'beristri', 'bersuami', 'istri saya',
                               'suami saya'],
                     'Cerai Hidup': ['cerai hidup', 'sudah cerai', 'bercerai', 'janda', 'duda'],
                     'Cerai Mati': ['cerai mati', 'meninggal', 'almarhum', 'almarhumah']}
METODE_KATA = {'digital': ['digital', 'pdf', 'online', 'daring', 'elektronik', 'soft file', 'softfile', 'email'],
               'basah': ['basah', 'cetak', 'print', 'kertas', 'fisik', 'hardcopy', 'hard copy', 'ambil langsung',
                         'ambil ke']}


def _keyword_grounded(value, story, table):
    low = normalize(story)
    for kata in table.get(value, []):
        if kata in low:
            # "belum menikah" tidak boleh dihitung sebagai bukti "Kawin"
            if value == 'Kawin' and re.search(r'belum\s+(menikah|kawin)', low):
                continue
            return True, _find_quote(story, [kata.split()[0]])
    return False, None


def ground_field(field, value, story, ai_quote=None):
    """Apakah nilai AI punya bukti di cerita warga? -> (True/False, kutipan_bukti)."""
    if ai_quote:  # kutipan dari AI harus benar-benar ada di cerita (bukan kutipan karangan)
        if normalize(ai_quote) not in normalize(story):
            return False, None
    if field == 'jenis_kelamin':
        return _keyword_grounded(value, story, JENIS_KELAMIN_KATA)
    if field == 'status_kawin':
        return _keyword_grounded(value, story, STATUS_KAWIN_KATA)
    if field == 'metode_tanda_tangan':
        return _keyword_grounded(value, story, METODE_KATA)
    if field == 'kewarganegaraan':
        low = normalize(story)
        ok = ('wni' in low or 'indonesia' in low) if value == 'WNI' else ('wna' in low or 'asing' in low)
        return ok, _find_quote(story, ['wni', 'indonesia', 'wna', 'asing']) if ok else None
    if field == 'tanggal_lahir':
        year = value[:4]
        return (year in story), (_find_quote(story, [year]) if year in story else None)
    if field == 'tempat_lahir':
        words = _words(value)
        ok = bool(words) and all(_word_in_story(w, _words(story)) for w in words)
        return ok, _find_quote(story, words) if ok else None
    return _text_grounded(value, story)


# ----------------------------------------------------------- 1. SOP

def detect_jenis(story, letter_types):
    """Kode jenis surat yang kata kuncinya muncul di cerita."""
    low = normalize(story)
    found = []
    for t in letter_types:
        sop = sop_for(t['kode_surat'], t.get('nama_surat'))
        if any(normalize(k) in low for k in sop['kata_kunci']):
            found.append(t['kode_surat'])
    return found


def canonical_tujuan(kode, value, story):
    """Tujuan resmi berdasarkan alias SOP bila warga menyebutnya (mis. "polsek" -> "Polsek Karang Pilang")."""
    low = normalize(story)
    alias = sop_for(kode)['tujuan_alias']
    value_low = normalize(value or '')
    for kata, resmi in alias.items():
        if kata in low and (not value or kata in value_low or normalize(resmi) == value_low):
            return resmi
    return None


def check_sop(kode, field, value):
    """Nilai melanggar SOP? -> alasan (str) atau None bila sesuai."""
    if field == 'tujuan' and kode:
        pola = sop_for(kode)['tujuan_pola']
        if pola and not re.search(pola, value, re.IGNORECASE):
            return f'Tujuan surat {kode} menurut SOP harus instansi yang berwenang'
    return None


def ground_tujuan(kode, value, story):
    """Tujuan: cocok alias SOP, atau semua nama diri di nilai ada di cerita."""
    resmi = canonical_tujuan(kode, value, story) if kode else None
    if resmi:
        return True, resmi, _find_quote(story, [k for k in sop_for(kode)['tujuan_alias'] if k in normalize(story)])
    ok, quote = _text_grounded(value, story, extra_exempt=wilayah_words())
    return ok, value, quote


# ----------------------------------------------------------- 2. intent

INTENTS = ('ajukan_surat', 'pertanyaan_umum', 'di_luar_layanan')
KEYAKINAN = ('tinggi', 'sedang', 'rendah')
_SURAT_HINT = re.compile(r'\bsurat\b|pengantar|keterangan|\bsk\b|mengurus|urus|bikin|buat(kan)?|ajukan|perlu', re.I)


def detect_intent(raw_intent, raw_keyakinan, story, matched_jenis):
    """Gabungkan intent dari AI dengan bukti di cerita. Server yang memutuskan."""
    intent = raw_intent if raw_intent in INTENTS else 'ajukan_surat'
    keyakinan = raw_keyakinan if raw_keyakinan in KEYAKINAN else 'sedang'
    if len(matched_jenis) == 1:
        # warga jelas menyebut satu jenis surat -> pasti pengajuan, walau AI bilang lain
        return 'ajukan_surat', ('tinggi' if keyakinan == 'tinggi' else 'sedang')
    if len(matched_jenis) > 1:
        return 'ajukan_surat', 'rendah'  # beberapa jenis surat disebut -> ambigu
    if intent == 'ajukan_surat' and not _SURAT_HINT.search(story):
        # AI menganggap pengajuan padahal tidak ada petunjuk surat sama sekali
        return 'ajukan_surat', 'rendah'
    return intent, keyakinan
