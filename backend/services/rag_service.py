import datetime
import logging
import math
import re
import time
import urllib.parse
from collections import Counter

from config import Config
from database.db import query_all

logger = logging.getLogger(__name__)
from services.chatbot_rules import (
    MIN_LOCAL_COVERAGE,
    aksi_dokumen,
    aksi_pertanyaan,
    batasan,
    build_escalation_summary,
    cek_keamanan,
    coverage_score,
    is_local_context_question,
    is_rt_surat_question,
    is_sensitive_credential_for_storage,
    klarifikasi_layanan_umum,
    mask_pii,
    normalisasi,
    semua_topik,
    topik_dokumen,
    topik_pertanyaan,
)
from services.semantic_embedding_service import (
    EmbeddingServiceUnavailableError,
    generate_embedding,
    is_embedding_configured,
    search_semantic_chunks,
)
from services.tanyart_llm_service import (
    is_gemini_configured,
    synthesize_answer_with_gemini,
    build_citation,
)


INDONESIAN_STOPWORDS = {
    'yang', 'di', 'dan', 'ini', 'itu', 'ke', 'dari', 'untuk', 'pada', 'dengan',
    'adalah', 'sebagai', 'dalam', 'bisa', 'dapat', 'oleh', 'ada', 'akan', 'atau',
    'saya', 'kami', 'kita', 'mereka', 'dia', 'apakah', 'bagaimana', 'apa', 'siapa',
    'berapa', 'kapan', 'dimana', 'kenapa', 'mengapa', 'mana', 'ya'
}

# Boost terkalibrasi untuk dokumen yang topik/aksinya cocok dengan pertanyaan.
TOPIK_BOOST = 0.10
AKSI_BOOST = 0.15
ACTION_CONFLICT_PENALTY = -0.25
LOCAL_RT_BOOST = 0.20

# Batas bawah skor mentah agar dokumen dengan topik cocok tetapi sangat lemah
# tidak langsung dianggap jawaban valid.
MIN_TOPIC_SCORE = 0.30
MIN_MARGIN = 0.05


def simple_stem(word: str) -> str:
    """Stemming sederhana untuk afiks dasar Bahasa Indonesia."""
    for p in ['se', 'ber', 'pe', 'di', 'ter', 'ke', 'per']:
        if word.startswith(p) and len(word) > len(p) + 2:
            word = word[len(p):]
            break
    for s in ['nya', 'kan', 'an', 'i', 'lah', 'kah']:
        if word.endswith(s) and len(word) > len(s) + 2:
            word = word[:-len(s)]
            break
    return word


def tokenize(text: str) -> list[str]:
    """Tokenisasi teks bahasa Indonesia menjadi token bersih tanpa tanda baca."""
    norm_text = normalisasi(text)
    cleaned = re.sub(r'[^\w\s]', ' ', norm_text)
    words = cleaned.split()
    return [w for w in words if len(w) > 1 and w not in INDONESIAN_STOPWORDS]


_CHUNKS_CACHE: list | None = None
_CHUNKS_CACHE_TIME: float = 0.0
CHUNKS_CACHE_TTL: float = 60.0  # cache 60 detik untuk memotong latensi roundtrip database
_last_query_all = None


def invalidate_knowledge_chunks_cache():
    """Hapus cache knowledge chunk agar termutakhirkan saat ada perubahan dokumen."""
    global _CHUNKS_CACHE, _CHUNKS_CACHE_TIME
    _CHUNKS_CACHE = None
    _CHUNKS_CACHE_TIME = 0.0


def get_knowledge_chunks(force_refresh: bool = False) -> list:
    """Ambil potongan dokumen dari cache in-memory atau query database bila cache habis."""
    global _CHUNKS_CACHE, _CHUNKS_CACHE_TIME, _last_query_all
    now = time.perf_counter()
    # Otomatis invalidate bila query_all distub oleh unit test
    if query_all is not _last_query_all:
        _CHUNKS_CACHE = None
        _last_query_all = query_all
    if force_refresh or _CHUNKS_CACHE is None or (now - _CHUNKS_CACHE_TIME) > CHUNKS_CACHE_TTL:
        _CHUNKS_CACHE = query_all("""
            SELECT c.chunk_id, c.knowledge_id, c.urutan_chunk, c.isi_chunk,
                   c.kata_kunci, c.kode_sumber, c.embedding_vector,
                   k.judul AS judul_dokumen, k.kategori, k.isi_dokumen AS document_text
            FROM knowledgechunk c
            JOIN knowledgebase k ON c.knowledge_id = k.knowledge_id
        """)
        _CHUNKS_CACHE_TIME = now
    return _CHUNKS_CACHE or []


def compute_cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Menghitung cosine similarity antara dua vektor TF."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator) / denominator


NAMA_BULAN = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]


def calculate_first_sunday(year: int, month: int) -> datetime.date:
    d = datetime.date(year, month, 1)
    days = (6 - d.weekday()) % 7
    return d + datetime.timedelta(days=days)


def calculate_kerja_bakti_calendar(query: str, ref_date: datetime.date | None = None) -> dict:
    """Hitung tanggal otomatis jadwal kerja bakti rutin hari Minggu pertama.

    Waktu acuan default menggunakan Asia/Jakarta (WIB) atau tanggal acuan eksplisit
    untuk pengujian deterministik.
    """
    if ref_date is None:
        try:
            import zoneinfo
            wib_now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Jakarta"))
            ref_date = wib_now.date()
        except Exception:
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            wib_now = utc_now + datetime.timedelta(hours=7)
            ref_date = wib_now.date()

    q_lower = query.lower()

    # Periksa apakah kueri menanyakan detail jam, titik kumpul, perlengkapan, atau kepastian
    is_asking_details = bool(re.search(
        r'\b(jam|pukul|mulai jam|titik kumpul|lokasi kumpul|tempat kumpul|perlengkapan|peralatan|alat|bawa apa|kepastian)\b',
        q_lower,
    ))

    # Deteksi bulan eksplisit dalam kueri
    detected_month = None
    for idx, m_name in enumerate(NAMA_BULAN):
        if m_name and m_name.lower() in q_lower:
            detected_month = idx
            break

    y_match = re.search(r'\b(20\d\d)\b', q_lower)
    detected_year = int(y_match.group(1)) if y_match else None

    # Bulan tanpa tahun yang ambigu diklarifikasi singkat
    if detected_month and not detected_year and not ('bulan ini' in q_lower or 'bulan depan' in q_lower):
        if detected_month != ref_date.month:
            rule_txt = Config.KERJA_BAKTI_SCHEDULE['rule_text']
            clarification_text = (
                f"{rule_txt} "
                f"Mohon sebutkan tahun yang Anda maksud untuk bulan {NAMA_BULAN[detected_month]} "
                f"(misalnya {NAMA_BULAN[detected_month]} {ref_date.year} atau {NAMA_BULAN[detected_month]} {ref_date.year + 1})."
            )
            return {
                'answer': clarification_text,
                'status': 'KLARIFIKASI_DIBUTUHKAN',
                'is_escalated': False,
                'target_date': None,
                'target_formatted': None,
            }

    is_bulan_ini = ('bulan ini' in q_lower)
    is_bulan_depan = ('bulan depan' in q_lower)

    if detected_month and detected_year:
        target_year = detected_year
        target_month = detected_month
    elif is_bulan_depan:
        target_year = ref_date.year + 1 if ref_date.month == 12 else ref_date.year
        target_month = 1 if ref_date.month == 12 else ref_date.month + 1
    else:
        target_year = ref_date.year
        target_month = ref_date.month

    target_sunday = calculate_first_sunday(target_year, target_month)
    target_formatted = f"Minggu, {target_sunday.day} {NAMA_BULAN[target_sunday.month]} {target_sunday.year}"

    # Hitung jadwal rutin berikutnya (Minggu pertama terdekat mulai hari ini)
    this_month_sunday = calculate_first_sunday(ref_date.year, ref_date.month)
    if ref_date <= this_month_sunday:
        next_routine_sunday = this_month_sunday
    else:
        nm = 1 if ref_date.month == 12 else ref_date.month + 1
        ny = ref_date.year + 1 if ref_date.month == 12 else ref_date.year
        next_routine_sunday = calculate_first_sunday(ny, nm)
    next_formatted = f"Minggu, {next_routine_sunday.day} {NAMA_BULAN[next_routine_sunday.month]} {next_routine_sunday.year}"

    # Susun teks jawaban sesuai kasus
    if is_asking_details and not re.search(r'\b(kapan|tanggal|hari apa)\b', q_lower):
        answer = (
            f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan (jadwal rutin berikutnya jatuh pada {next_formatted}). "
            "Namun informasi jam mulai dan titik kumpul kerja bakti belum tersedia di TanyaRT. "
            "Silakan konfirmasi kepada pengurus RT melalui tombol WhatsApp di bawah."
        )
    elif is_bulan_ini:
        if ref_date == target_sunday:
            answer = f"Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} jatuh pada hari ini, {target_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."
        elif ref_date > target_sunday:
            answer = f"Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} jatuh pada {target_formatted} dan sudah lewat. Jadwal rutin berikutnya adalah {next_formatted}."
        else:
            answer = f"Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} dijadwalkan pada {target_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."
    elif (detected_month and detected_year) or is_bulan_depan:
        if ref_date == target_sunday:
            answer = f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan. Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} jatuh pada hari ini, {target_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."
        elif ref_date > target_sunday:
            answer = f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan. Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} jatuh pada {target_formatted} dan sudah lewat. Jadwal rutin berikutnya adalah {next_formatted}."
        else:
            answer = f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan. Jadwal rutin bulan {NAMA_BULAN[target_month]} {target_year} jatuh pada {target_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."
    else:
        # Jadwal umum / berikutnya
        if ref_date == next_routine_sunday:
            answer = f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan. Jadwal rutin jatuh pada hari ini, {next_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."
        else:
            answer = f"Kerja bakti rutin dilaksanakan setiap Minggu pertama setiap bulan. Jadwal rutin berikutnya jatuh pada {next_formatted}. Untuk jam dan titik kumpul, silakan konfirmasi kepada pengurus RT."

    return {
        'answer': answer,
        'status': 'SUMBER_DITEMUKAN',
        'is_escalated': True,
        'target_date': target_sunday,
        'target_formatted': target_formatted,
        'next_date': next_routine_sunday,
        'next_formatted': next_formatted,
        'month_name': NAMA_BULAN[target_month],
        'year': target_year,
    }


def _whatsapp_url(summary: str | None = None) -> str | None:
    """Bentuk URL WhatsApp eskalasi dengan salam, ringkasan pertanyaan, dan penutup resmi (SRS REQ-6)."""
    if not Config.RT_WHATSAPP_NUMBER:
        return None

    clean_number = re.sub(r'\D', '', str(Config.RT_WHATSAPP_NUMBER))
    if not clean_number:
        return None

    if not summary:
        summary = "Pertanyaan seputar layanan administrasi warga."

    message = (
        "Halo Pak/Bu RT, saya ingin menanyakan hal berikut:\n\n"
        f"{summary}\n\n"
        "Mohon informasi atau arahannya. Terima kasih."
    )
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean_number}?text={encoded}"


def _contact_suffix() -> str:
    if Config.RT_WHATSAPP_NUMBER:
        return " Silakan hubungi Ketua RT melalui tombol WhatsApp di bawah."
    return " Silakan hubungi Ketua RT secara langsung."


MESSAGES = {
    'RAHASIA': (
        "Maaf, informasi rahasia seperti PIN, OTP, atau kata sandi tidak dapat "
        "dibagikan melalui chatbot."
    ),
    'LUAR_CAKUPAN': (
        "Maaf, pertanyaan tersebut di luar cakupan layanan administrasi RT/RW."
    ),
    'BELUM_ADA_SOP_RT': (
        "Maaf, SOP lokal RT untuk hal ini belum tersedia di basis data resmi."
    ),
    'PERLU_VERIFIKASI': (
        "Maaf, saya belum menemukan sumber yang cukup yakin untuk menjawab "
        "pertanyaan tersebut."
    ),
    'PERTANYAAN_TIDAK_JELAS': (
        "Pertanyaan tidak dapat dipahami. Silakan masukkan pertanyaan yang lebih jelas."
    ),
}


def _fallback_result(query, status, best_score=0.0, summary=None):
    message = MESSAGES.get(status, MESSAGES['PERLU_VERIFIKASI'])
    if status not in ('RAHASIA', 'PERTANYAAN_TIDAK_JELAS'):
        message += _contact_suffix()

    if status == 'RAHASIA':
        wa_url = None
        safe_summary = None
    else:
        safe_summary = summary or build_escalation_summary(query)
        wa_url = _whatsapp_url(safe_summary)

    return {
        'is_escalated': True,
        'answer': message,
        'citation': None,
        'similarity_score': round(min(max(best_score, 0.0), 1.0), 4),
        'top_chunk_id': None,
        'source_id': None,
        'status': status,
        'escalation_whatsapp_url': wa_url,
        'escalation_summary': safe_summary,
    }


def format_grounded_chunk_result(
    query: str,
    chunk: dict,
    similarity_score: float,
    base_score: float,
    topic_match: bool = False,
    action_match: bool = False,
    retrieval_mode: str = 'lexical_heuristic_fallback',
    ref_date: datetime.date | None = None,
    query_efektif: str | None = None,
    history: list | None = None,
) -> dict:
    """Format hasil jawaban terikat sumber untuk dokumen yang berhasil diambil.

    Memastikan konsistensi penanganan iuran, kerja bakti, dan eskalasi pada jalur
    semantik maupun leksikal tanpa memaksa retrieval gagal (skor tetap skor aktual retrieval).
    """
    judul = chunk.get('judul_dokumen') or chunk.get('judul') or 'Pedoman RT'
    urutan = chunk.get('urutan_chunk') or 1
    is_local = not bool(chunk.get('kode_sumber'))
    isi_chunk = str(chunk.get('isi_chunk') or '').strip()
    c_lower = isi_chunk.lower()
    q_norm = normalisasi(query)

    citation = build_citation(chunk)
    display_judul = judul

    # 1. Kasus iuran lingkungan RT
    if re.search(r'\biuran\b', q_norm) and 'iuran kas kebersihan' in c_lower:
        # Jika hanya menanyakan jadwal jatuh tempo rutin (kapan iuran dibayar)
        if re.search(r'^kapan iuran', q_norm):
            return {
                'is_escalated': False,
                'answer': f'Berdasarkan {display_judul}: {isi_chunk}',
                'citation': citation,
                'similarity_score': round(min(max(similarity_score, 0.0), 1.0), 4),
                'base_score': round(base_score, 4),
                'top_chunk_id': chunk.get('chunk_id'),
                'source_id': chunk.get('kode_sumber'),
                'status': 'SUMBER_DITEMUKAN',
                'topic_match': topic_match,
                'action_match': action_match,
                'escalation_whatsapp_url': None,
                'retrieval_mode': retrieval_mode,
            }

        summary_text = build_escalation_summary(query, query_efektif=query_efektif, history=history, ref_date=ref_date)
        if re.search(r'\b(sudah bayar|sudah transfer|konfirmasi pembayaran|bukti transfer|konfirmasi bayar|cara konfirmasi|status bayar)\b', q_norm):
            answer_text = (
                f'Berdasarkan {display_judul}: {isi_chunk} '
                'Namun prosedur konfirmasi dan pencatatan status pembayaran warga belum tercantum pada dokumen resmi. '
                'Silakan konfirmasi pembayaran Anda kepada pengurus RT melalui tombol WhatsApp di bawah.'
            )
        elif re.search(r'\b(keringanan|keberatan|potongan|diskon|minta keringanan|tidak mampu)\b', q_norm):
            answer_text = (
                f'Berdasarkan {display_judul}: {isi_chunk} '
                'Namun ketentuan mengenai permohonan keringanan iuran belum tercantum pada dokumen resmi. '
                'Silakan hubungi pengurus RT melalui tombol WhatsApp di bawah.'
            )
        else:
            answer_text = (
                f'Berdasarkan {display_judul}: {isi_chunk} '
                'Namun rincian nominal iuran resmi yang berlaku saat ini serta pencatatan status pembayaran iuran warga per bulan belum tercantum pada dokumen resmi. '
                'Silakan konfirmasi ke Ketua RT melalui tombol WhatsApp di bawah.'
            )
        return {
            'is_escalated': True,
            'answer': answer_text,
            'citation': citation,
            'similarity_score': round(min(max(similarity_score, 0.0), 1.0), 4),
            'base_score': round(base_score, 4),
            'top_chunk_id': chunk.get('chunk_id'),
            'source_id': chunk.get('kode_sumber'),
            'status': 'SUMBER_DITEMUKAN',
            'topic_match': topic_match,
            'action_match': action_match,
            'escalation_whatsapp_url': _whatsapp_url(summary_text),
            'escalation_summary': summary_text,
            'retrieval_mode': retrieval_mode,
        }

    # 1b. Kasus persyaratan khusus pengantar RT untuk SKCK yang belum tercatat
    if (re.search(r'\bskck\b', q_norm) or chunk.get('kode_sumber') in ('RTC-025', 'RTC-026', 'RTC-032')) and re.search(r'\bpengantar\b', q_norm):
        summary_text = build_escalation_summary(query, query_efektif=query_efektif, history=history, ref_date=ref_date)
        answer_text = (
            f'Berdasarkan {display_judul}: {isi_chunk} '
            'Surat SKCK diterbitkan oleh pihak kepolisian (Polri), dan pengantar RT tidak selalu diwajibkan untuk semua kategori. '
            'Persyaratan khusus surat pengantar RT untuk keperluan SKCK belum tercantum pada dokumen resmi. '
            'Silakan konfirmasi kepada pengurus RT melalui tombol WhatsApp di bawah.'
        )
        return {
            'is_escalated': True,
            'answer': answer_text,
            'citation': citation,
            'similarity_score': round(min(max(similarity_score, 0.0), 1.0), 4),
            'base_score': round(base_score, 4),
            'top_chunk_id': chunk.get('chunk_id'),
            'source_id': chunk.get('kode_sumber'),
            'status': 'SUMBER_DITEMUKAN',
            'topic_match': topic_match,
            'action_match': action_match,
            'escalation_whatsapp_url': _whatsapp_url(summary_text),
            'escalation_summary': summary_text,
            'retrieval_mode': retrieval_mode,
        }

    # 2. Kasus kerja bakti lingkungan RT
    if re.search(r'\bkerja bakti\b', q_norm) and 'kerja bakti' in c_lower:
        summary_text = build_escalation_summary(query, query_efektif=query_efektif, history=history, ref_date=ref_date)
        cal_res = calculate_kerja_bakti_calendar(query, ref_date=ref_date)

        answer_text = f"Berdasarkan {display_judul}: {cal_res['answer']}"
        is_clarif = (cal_res.get('status') == 'KLARIFIKASI_DIBUTUHKAN')

        return {
            'is_escalated': cal_res.get('is_escalated', True),
            'answer': answer_text,
            'citation': citation,
            'similarity_score': round(min(max(similarity_score, 0.0), 1.0), 4),
            'base_score': round(base_score, 4),
            'top_chunk_id': chunk.get('chunk_id'),
            'source_id': chunk.get('kode_sumber'),
            'status': cal_res.get('status', 'SUMBER_DITEMUKAN'),
            'topic_match': topic_match,
            'action_match': action_match,
            'escalation_whatsapp_url': _whatsapp_url(summary_text) if not is_clarif else None,
            'escalation_summary': summary_text if not is_clarif else None,
            'retrieval_mode': retrieval_mode,
            'answer_type': 'rule_based_calendar',
        }

    # 3. Kasus dokumen standar umum (KTP, KK, SKCK, NIB, dll)
    if is_local and chunk.get('document_text'):
        answer_body = re.sub(r'\s+', ' ', chunk['document_text']).strip()
    else:
        answer_body = re.sub(r'^\d+\.\s*', '', isi_chunk)

    return {
        'is_escalated': False,
        'answer': f'Berdasarkan {display_judul}: {answer_body}',
        'citation': citation,
        'similarity_score': round(min(max(similarity_score, 0.0), 1.0), 4),
        'base_score': round(base_score, 4),
        'top_chunk_id': chunk.get('chunk_id'),
        'source_id': chunk.get('kode_sumber'),
        'status': 'SUMBER_DITEMUKAN',
        'topic_match': topic_match,
        'action_match': action_match,
        'escalation_whatsapp_url': None,
        'retrieval_mode': retrieval_mode,
    }


def _answered_result(ranked_best, query="", query_efektif=None, history=None):
    return format_grounded_chunk_result(
        query=query,
        chunk=ranked_best['chunk'],
        similarity_score=ranked_best['ranking_score'],
        base_score=ranked_best['base_score'],
        topic_match=ranked_best['topic_match'],
        action_match=ranked_best['action_match'],
        retrieval_mode='lexical_heuristic_fallback',
        query_efektif=query_efektif,
        history=history,
    )


def search_chunks(
    query: str,
    chunks: list,
    query_efektif: str | None = None,
    history: list | None = None,
):
    """Rank chunks tanpa menyentuh database.

    Dipakai oleh API (setelah query DB) dan oleh evaluasi runtime.
    """
    sec_guard = cek_keamanan(query)
    if sec_guard:
        return _fallback_result(query, sec_guard)

    # Deteksi klarifikasi layanan umum (mis. mau mengurus KTP tanpa detail keperluan)
    eff = query_efektif or query
    klarif = klarifikasi_layanan_umum(eff)
    if not klarif and query != eff:
        klarif = klarifikasi_layanan_umum(query)
    if klarif:
        if isinstance(klarif, dict):
            summary_text = build_escalation_summary(query, query_efektif=query_efektif, history=history)
            return {
                'is_escalated': klarif.get('is_escalated', False),
                'answer': klarif['answer'],
                'citation': klarif.get('citation'),
                'similarity_score': 0.0,
                'top_chunk_id': None,
                'source_id': None,
                'status': klarif.get('status', 'KLARIFIKASI_DIBUTUHKAN'),
                'escalation_whatsapp_url': _whatsapp_url(summary_text) if klarif.get('is_escalated') else None,
                'escalation_summary': summary_text if klarif.get('is_escalated') else None,
                'retrieval_mode': 'clarification',
            }
        return {
            'is_escalated': False,
            'answer': klarif,
            'citation': None,
            'similarity_score': 0.0,
            'top_chunk_id': None,
            'source_id': None,
            'status': 'KLARIFIKASI_DIBUTUHKAN',
            'escalation_whatsapp_url': None,
            'retrieval_mode': 'clarification',
        }

    search_q = query_efektif if query_efektif else query
    all_topics = semua_topik(search_q)
    if len(all_topics) > 1:
        # Multi-topik: jika kueri mencakup > 1 topik independen, minta klarifikasi / eskalasi
        return _fallback_result(query, 'PERLU_VERIFIKASI')

    q_norm = normalisasi(search_q)
    query_tokens = tokenize(search_q)
    if not query_tokens:
        return _fallback_result(query, 'PERTANYAAN_TIDAK_JELAS')

    q_stems = [simple_stem(w) for w in query_tokens]
    query_vec = Counter(query_tokens)
    intent_topic = all_topics[0] if all_topics else None
    intent_action = aksi_pertanyaan(search_q)
    local_context = is_local_context_question(search_q)
    rt_surat = is_rt_surat_question(search_q)

    ranked = []
    for chunk in chunks:
        combined_text = (
            f"{chunk.get('isi_chunk', '')} "
            f"{chunk.get('kata_kunci') or ''} "
            f"{chunk.get('judul_dokumen', '')}"
        )
        chunk_tokens = tokenize(combined_text)
        if not chunk_tokens:
            continue

        c_stems = [simple_stem(w) for w in chunk_tokens]
        chunk_vec = Counter(chunk_tokens)
        cos_score = compute_cosine_similarity(query_vec, chunk_vec)

        matched_stems = sum(
            1 for qs in q_stems
            if any(
                qs == cs
                or (len(qs) >= 3 and qs in cs)
                or (len(cs) >= 3 and cs in qs)
                for cs in c_stems
            )
        )
        recall_score = matched_stems / len(q_stems) if q_stems else 0.0
        base_score = min(
            max(cos_score, (recall_score * 0.75) + (cos_score * 0.25)),
            1.0,
        )

        source_id = chunk.get('kode_sumber')
        is_local = not bool(source_id)
        doc_topic = topik_dokumen(source_id)
        if is_local:
            c_isi_lower = chunk.get('isi_chunk', '').lower()
            if 'iuran' in c_isi_lower:
                doc_topic = 'iuran'
            elif 'kerja bakti' in c_isi_lower:
                doc_topic = 'kerja_bakti'
        doc_action = aksi_dokumen(source_id)
        topic_match = bool(intent_topic and doc_topic == intent_topic)
        action_match = bool(
            topic_match and intent_action and doc_action == intent_action
        )

        boost = TOPIK_BOOST if topic_match else 0.0
        if action_match:
            boost += AKSI_BOOST
        elif intent_action and doc_action:
            # Penalti konflik aksi hanya untuk pasangan aksi yang bertentangan langsung (hilang vs rusak)
            if (intent_action == 'hilang' and doc_action == 'rusak') or (
                intent_action == 'rusak' and doc_action == 'hilang'
            ):
                boost += ACTION_CONFLICT_PENALTY
        if local_context and is_local:
            boost += LOCAL_RT_BOOST

        ranked.append({
            'chunk': chunk,
            'base_score': base_score,
            'ranking_score': base_score + boost,
            'topic_match': topic_match,
            'action_match': action_match,
            'is_local': is_local,
            'coverage': (
                coverage_score(
                    search_q,
                    chunk.get('document_text') or combined_text,
                )
                if is_local else 0.0
            ),
        })

    if not ranked:
        return _fallback_result(query, 'PERLU_VERIFIKASI')

    ranked.sort(
        key=lambda item: (
            -item['ranking_score'],
            -item['base_score'],
            str(item['chunk'].get('chunk_id', '')),
        )
    )

    best = ranked[0]

    # Untuk pertanyaan SOP RT, prioritaskan kandidat lokal yang kata-kata
    # pentingnya benar-benar tercakup, bukan dokumen pemerintah yang kebetulan
    # memiliki frasa umum serupa.
    if rt_surat:
        local_candidates = [
            item for item in ranked
            if item['is_local'] and item['coverage'] >= MIN_LOCAL_COVERAGE
        ]
        if local_candidates:
            best = local_candidates[0]
    elif local_context:
        if re.search(r'\biuran\b', q_norm):
            iuran_cand = [
                it for it in ranked
                if it['is_local'] and 'iuran kas kebersihan' in it['chunk'].get('isi_chunk', '').lower()
            ]
            if iuran_cand:
                best = iuran_cand[0]
        elif re.search(r'\bkerja bakti\b', q_norm):
            kb_cand = [
                it for it in ranked
                if it['is_local'] and 'kerja bakti' in it['chunk'].get('isi_chunk', '').lower()
            ]
            if kb_cand:
                best = kb_cand[0]

    others = [item for item in ranked if item is not best]
    second = others[0] if others else None
    margin = (
        best['ranking_score'] - second['ranking_score']
        if second else best['ranking_score']
    )

    guard = batasan(
        search_q,
        best_score=best['ranking_score'],
        answer_threshold=Config.RAG_SIMILARITY_THRESHOLD,
        best_is_local=best['is_local'],
        best_base_score=best['base_score'],
        best_coverage=best['coverage'],
    )
    if guard:
        return _fallback_result(query, guard, best_score=best['base_score'])

    # Untuk dokumen domisili (RTC-019 kontrakan vs RTC-020 verifikasi alamat),
    # pertanyaan umum tanpa aksi spesifik tidak boleh dijawab sepihak.
    doc_id = best['chunk'].get('kode_sumber')
    if doc_id in ('RTC-019', 'RTC-020') and not best['action_match']:
        return _fallback_result(query, 'PERLU_VERIFIKASI', best_score=best['base_score'])

    local_subject_match = True
    if re.search(r'\biuran\b', q_norm) and 'iuran' not in best['chunk'].get('isi_chunk', '').lower():
        local_subject_match = False
    if re.search(r'\bkerja bakti\b', q_norm) and 'kerja bakti' not in best['chunk'].get('isi_chunk', '').lower():
        local_subject_match = False

    topic_answer = (
        best['topic_match'] and best['base_score'] >= MIN_TOPIC_SCORE
    )
    score_answer = (
        best['ranking_score'] >= Config.RAG_SIMILARITY_THRESHOLD
        and margin >= MIN_MARGIN
        and local_subject_match
    )
    local_sop_answer = (
        rt_surat
        and best['is_local']
        and best['coverage'] >= MIN_LOCAL_COVERAGE
    )
    local_context_answer = (
        local_context
        and best['is_local']
        and local_subject_match
        and best['ranking_score'] >= Config.RAG_SIMILARITY_THRESHOLD
    )

    if topic_answer or score_answer or local_sop_answer or local_context_answer:
        return _answered_result(best, query=query, query_efektif=query_efektif, history=history)

    safe_summary = build_escalation_summary(query, query_efektif=query_efektif, history=history)
    return _fallback_result(
        query, 'PERLU_VERIFIKASI', best_score=best['base_score'], summary=safe_summary
    )


def search_knowledge_base(
    query: str,
    conversation_history: list | None = None,
    time_budget: float | None = None,
    raw_query: str | None = None,
) -> dict:
    """Cari jawaban pada knowledge base runtime Supabase.

    Sesuai SRS:
    - Batas Privasi: Memvalidasi kueri dan menyamarkan PII (NIK/No HP) sebelum
      percabangan semantik maupun leksikal. Kredensial rahasia / injeksi dicegat langsung.
    - Anggaran Waktu: Seluruh alur (embedding + LLM) berjalan dalam time budget (maks 5s).
    - Mode Ollama memakai pencarian leksikal dan menyusun jawaban dari dokumen terpilih.
    """
    t_start = time.perf_counter()
    budget = time_budget if time_budget is not None else Config.TANYART_LLM_TIMEOUT

    # 0. Evaluasi keamanan & privasi terpadu sebelum percabangan semantik/leksikal
    sec_guard = cek_keamanan(query)
    if not sec_guard and is_sensitive_credential_for_storage(query):
        sec_guard = 'RAHASIA'
    if sec_guard:
        return _fallback_result(query, sec_guard)

    # Masking PII pada kueri dan riwayat sebelum diteruskan ke embedding maupun LLM
    clean_query = mask_pii(query)
    citizen_query = mask_pii(raw_query) if raw_query else clean_query
    clean_history = [
        mask_pii(m) for m in (conversation_history or [])
        if m and '[Pesan disembunyikan' not in m and not is_sensitive_credential_for_storage(m)
    ]

    chunks = get_knowledge_chunks()

    # 1. Jalur Semantic Embedding (SRS REQ-3: text-embedding-3-small + Cosine Similarity)
    semantic_enabled = is_embedding_configured()
    chunks_with_vec = [c for c in (chunks or []) if c.get('embedding_vector')]

    semantic_status = None
    semantic_diagnostic = None

    if not semantic_enabled:
        semantic_status = 'unconfigured'
        semantic_diagnostic = 'Mode Ollama lokal: pencarian leksikal, embedding lokal belum tersedia'
    elif not chunks_with_vec:
        semantic_status = 'empty_vectors'
        semantic_diagnostic = f'Database memuat {len(chunks or [])} chunk, namun seluruhnya belum memiliki embedding_vector'
    else:
        rem_budget = budget - (time.perf_counter() - t_start)
        if rem_budget <= 0.05:
            semantic_status = 'timeout'
            semantic_diagnostic = 'Anggaran waktu habis sebelum memanggil layanan embedding'
        else:
            try:
                q_vec = generate_embedding(clean_query, timeout=rem_budget)
                best_chunk, cosine_sim, ranked_sem = search_semantic_chunks(
                    q_vec, chunks_with_vec, threshold=Config.RAG_SIMILARITY_THRESHOLD
                )
                if best_chunk:
                    semantic_status = 'success'
                    semantic_diagnostic = f'Pencarian semantik berhasil (cosine_score={cosine_sim:.4f} >= {Config.RAG_SIMILARITY_THRESHOLD})'
                    res = format_grounded_chunk_result(
                        citizen_query,
                        best_chunk,
                        similarity_score=cosine_sim,
                        base_score=cosine_sim,
                        topic_match=True,
                        action_match=True,
                        retrieval_mode='semantic_embedding',
                        query_efektif=clean_query,
                        history=clean_history,
                    )
                    res['semantic_status'] = semantic_status
                    res['semantic_diagnostic'] = semantic_diagnostic
                    if not res.get('is_escalated'):
                        rem_for_llm = budget - (time.perf_counter() - t_start)
                        if rem_for_llm > 0.05:
                            answer_llm, citation, used_llm = synthesize_answer_with_gemini(
                                clean_query, best_chunk, clean_history, time_budget=rem_for_llm
                            )
                            res['answer'] = answer_llm
                            res['citation'] = citation
                            res['ai_generated'] = used_llm
                            if not used_llm and is_gemini_configured():
                                res['is_escalated'] = True
                                summary_text = build_escalation_summary(citizen_query, query_efektif=clean_query, history=clean_history)
                                res['escalation_whatsapp_url'] = _whatsapp_url(summary_text)
                                res['escalation_summary'] = summary_text
                        else:
                            res['ai_generated'] = False
                            if is_gemini_configured():
                                res['is_escalated'] = True
                                summary_text = build_escalation_summary(citizen_query, query_efektif=clean_query, history=clean_history)
                                res['escalation_whatsapp_url'] = _whatsapp_url(summary_text)
                                res['escalation_summary'] = summary_text
                    return res
                else:
                    semantic_status = 'below_threshold'
                    semantic_diagnostic = f'Skor semantik tertinggi ({cosine_sim:.4f}) di bawah ambang batas {Config.RAG_SIMILARITY_THRESHOLD}'
                    summary_text = build_escalation_summary(citizen_query, query_efektif=clean_query, history=clean_history)
                    res = _fallback_result(citizen_query, 'PERLU_VERIFIKASI', best_score=cosine_sim, summary=summary_text)
                    res['retrieval_mode'] = 'semantic_embedding'
                    res['semantic_status'] = semantic_status
                    res['semantic_diagnostic'] = semantic_diagnostic
                    return res
            except EmbeddingServiceUnavailableError as err:
                err_str = str(err)
                if '429' in err_str or 'quota' in err_str.lower() or 'credits' in err_str.lower():
                    semantic_status = 'api_failure:quota_exhausted'
                    semantic_diagnostic = 'Panggilan embedding gagal: kuota OpenAI habis (HTTP 429 Insufficient Quota)'
                elif 'timeout' in err_str.lower():
                    semantic_status = 'timeout'
                    semantic_diagnostic = 'Panggilan embedding melebihi batas waktu (timeout)'
                else:
                    semantic_status = f'api_failure:{type(err).__name__}'
                    semantic_diagnostic = f'Panggilan embedding gagal ({type(err).__name__})'
                logger.warning("Panggilan embedding semantik dialihkan ke leksikal: %s", semantic_diagnostic)
            except Exception as err:
                semantic_status = f'api_failure:{type(err).__name__}'
                semantic_diagnostic = f'Panggilan embedding gagal ({type(err).__name__})'
                logger.warning("Panggilan embedding semantik dialihkan ke leksikal: %s", semantic_diagnostic)

    # 2. Jalur Lexical Heuristic Fallback (bila embedding belum aktif/tersedia/gagal)
    res = search_chunks(citizen_query, chunks or [], query_efektif=clean_query, history=clean_history)
    res['retrieval_mode'] = 'lexical_heuristic_fallback'
    res['semantic_status'] = semantic_status or 'fallback'
    res['semantic_diagnostic'] = semantic_diagnostic

    # 3. Bila sumber ditemukan, sintesis jawaban dengan Gemini (SRS REQ-5)
    if res.get('status') == 'SUMBER_DITEMUKAN' and res.get('top_chunk_id') and not res.get('is_escalated'):
        matched_chunk = next(
            (c for c in (chunks or []) if c.get('chunk_id') == res['top_chunk_id']),
            None,
        )
        if matched_chunk:
            rem_for_llm = budget - (time.perf_counter() - t_start)
            if rem_for_llm > 0.05:
                answer_llm, citation, used_llm = synthesize_answer_with_gemini(
                    clean_query, matched_chunk, clean_history, time_budget=rem_for_llm
                )
                res['answer'] = answer_llm
                res['citation'] = citation
                res['ai_generated'] = used_llm
                if not used_llm and is_gemini_configured():
                    res['is_escalated'] = True
                    summary_text = build_escalation_summary(citizen_query, query_efektif=clean_query, history=clean_history)
                    res['escalation_whatsapp_url'] = _whatsapp_url(summary_text)
                    res['escalation_summary'] = summary_text
            else:
                res['ai_generated'] = False
                if is_gemini_configured():
                    res['is_escalated'] = True
                    summary_text = build_escalation_summary(citizen_query, query_efektif=clean_query, history=clean_history)
                    res['escalation_whatsapp_url'] = _whatsapp_url(summary_text)
                    res['escalation_summary'] = summary_text

    return res
