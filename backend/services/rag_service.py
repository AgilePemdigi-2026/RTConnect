import math
import re
import urllib.parse
from collections import Counter

from config import Config
from database.db import query_all
from services.chatbot_rules import (
    MIN_LOCAL_COVERAGE,
    aksi_dokumen,
    aksi_pertanyaan,
    batasan,
    coverage_score,
    is_local_context_question,
    is_rt_surat_question,
    topik_dokumen,
    topik_pertanyaan,
)


INDONESIAN_STOPWORDS = {
    'yang', 'di', 'dan', 'ini', 'itu', 'ke', 'dari', 'untuk', 'pada', 'dengan',
    'adalah', 'sebagai', 'dalam', 'bisa', 'dapat', 'oleh', 'ada', 'akan', 'atau',
    'saya', 'kami', 'kita', 'mereka', 'dia', 'apakah', 'bagaimana', 'apa', 'siapa',
    'berapa', 'kapan', 'dimana', 'kenapa', 'mengapa'
}

# Boost kecil untuk dokumen yang topik/aksinya cocok dengan pertanyaan.
TOPIK_BOOST = 0.10
AKSI_BOOST = 0.05
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
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    words = cleaned.split()
    return [w for w in words if len(w) > 1 and w not in INDONESIAN_STOPWORDS]


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


def _whatsapp_url(query: str, include_query: bool = True):
    if not Config.RT_WHATSAPP_NUMBER:
        return None
    if include_query:
        message = (
            f"Halo {Config.RT_NAME}, saya warga {Config.RT_AREA} "
            f"ingin menanyakan perihal: {query}"
        )
        return (
            f"https://wa.me/{Config.RT_WHATSAPP_NUMBER}"
            f"?text={urllib.parse.quote(message)}"
        )
    return f"https://wa.me/{Config.RT_WHATSAPP_NUMBER}"


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


def _fallback_result(query, status, best_score=0.0, include_query=True):
    message = MESSAGES.get(status, MESSAGES['PERLU_VERIFIKASI'])
    if status not in ('RAHASIA', 'PERTANYAAN_TIDAK_JELAS'):
        message += _contact_suffix()

    return {
        'is_escalated': True,
        'answer': message,
        'citation': None,
        'similarity_score': round(min(max(best_score, 0.0), 1.0), 4),
        'top_chunk_id': None,
        'source_id': None,
        'status': status,
        'escalation_whatsapp_url': _whatsapp_url(
            query, include_query=include_query
        ),
    }


def _answered_result(ranked_best):
    chunk = ranked_best['chunk']
    judul = chunk['judul_dokumen']
    urutan = chunk.get('urutan_chunk') or 1
    is_local = not bool(chunk.get('kode_sumber'))

    if is_local and chunk.get('document_text'):
        answer_body = re.sub(r'\s+', ' ', chunk['document_text']).strip()
        citation = judul
    else:
        answer_body = re.sub(r'^\d+\.\s*', '', chunk['isi_chunk'])
        citation = f"{judul} (Bagian {urutan})"

    return {
        'is_escalated': False,
        'answer': f"Berdasarkan {judul}: {answer_body}",
        'citation': citation,
        'similarity_score': round(min(ranked_best['ranking_score'], 1.0), 4),
        'base_score': round(ranked_best['base_score'], 4),
        'top_chunk_id': chunk.get('chunk_id'),
        'source_id': chunk.get('kode_sumber'),
        'status': 'SUMBER_DITEMUKAN',
        'topic_match': ranked_best['topic_match'],
        'action_match': ranked_best['action_match'],
        'escalation_whatsapp_url': None,
    }


def search_chunks(query, chunks):
    """Rank chunks tanpa menyentuh database.

    Dipakai oleh API (setelah query DB) dan oleh evaluasi runtime.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return _fallback_result(
            query, 'PERTANYAAN_TIDAK_JELAS', include_query=False
        )

    q_stems = [simple_stem(w) for w in query_tokens]
    query_vec = Counter(query_tokens)
    intent_topic = topik_pertanyaan(query)
    intent_action = aksi_pertanyaan(query)
    local_context = is_local_context_question(query)
    rt_surat = is_rt_surat_question(query)

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
        doc_action = aksi_dokumen(source_id)
        topic_match = bool(intent_topic and doc_topic == intent_topic)
        action_match = bool(
            topic_match and intent_action and doc_action == intent_action
        )

        boost = TOPIK_BOOST if topic_match else 0.0
        if action_match:
            boost += AKSI_BOOST
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
                    query,
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

    others = [item for item in ranked if item is not best]
    second = others[0] if others else None
    margin = (
        best['ranking_score'] - second['ranking_score']
        if second else best['ranking_score']
    )

    guard = batasan(
        query,
        best_score=best['ranking_score'],
        answer_threshold=Config.RAG_SIMILARITY_THRESHOLD,
        best_is_local=best['is_local'],
        best_base_score=best['base_score'],
        best_coverage=best['coverage'],
    )
    if guard:
        return _fallback_result(
            query,
            guard,
            best_score=best['base_score'],
            include_query=(guard != 'RAHASIA'),
        )

    topic_answer = (
        best['topic_match'] and best['base_score'] >= MIN_TOPIC_SCORE
    )
    score_answer = (
        best['ranking_score'] >= Config.RAG_SIMILARITY_THRESHOLD
        and margin >= MIN_MARGIN
    )
    local_sop_answer = (
        rt_surat
        and best['is_local']
        and best['coverage'] >= MIN_LOCAL_COVERAGE
    )

    if topic_answer or score_answer or local_sop_answer:
        return _answered_result(best)

    return _fallback_result(
        query, 'PERLU_VERIFIKASI', best_score=best['base_score']
    )


def search_knowledge_base(query: str) -> dict:
    """Cari jawaban pada knowledge base runtime.

    Skor yang dikembalikan adalah skor hybrid heuristik (lexical + boost
    topik/aksi), bukan probabilitas model.
    """
    chunks = query_all("""
        SELECT c.chunk_id, c.knowledge_id, c.urutan_chunk, c.isi_chunk,
               c.kata_kunci, c.kode_sumber,
               k.judul_dokumen, k.kategori, k.isi_dokumen AS document_text
        FROM knowledge_chunks c
        JOIN knowledge_base k ON c.knowledge_id = k.knowledge_id
    """)
    return search_chunks(query, chunks)
