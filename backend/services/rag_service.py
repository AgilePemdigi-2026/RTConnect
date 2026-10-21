import math
import re
import urllib.parse
from collections import Counter
from config import Config
from database.db import query_all

INDONESIAN_STOPWORDS = {
    'yang', 'di', 'dan', 'ini', 'itu', 'ke', 'dari', 'untuk', 'pada', 'dengan', 
    'adalah', 'sebagai', 'dalam', 'bisa', 'dapat', 'oleh', 'ada', 'akan', 'atau',
    'saya', 'kami', 'kita', 'mereka', 'dia', 'apakah', 'bagaimana', 'apa', 'siapa',
    'berapa', 'kapan', 'dimana', 'kenapa', 'mengapa'
}

def simple_stem(word: str) -> str:
    """Stemming sederhana untuk afiks dasar Bahasa Indonesia"""
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
    """Tokenisasi teks bahasa Indonesia menjadi token bersih tanpa tanda baca"""
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    words = cleaned.split()
    return [w for w in words if len(w) > 1 and w not in INDONESIAN_STOPWORDS]

def compute_cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Menghitung cosine similarity antara dua vektor TF"""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator) / denominator

def search_knowledge_base(query: str) -> dict:
    """
    Rank chunks with lexical cosine and Indonesian stem coverage.
    The returned score is a heuristic retrieval score, not model confidence.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return {
            'is_escalated': True,
            'answer': 'Pertanyaan tidak dapat dipahami. Silakan masukkan pertanyaan yang lebih jelas. '
                      + (f"Anda juga dapat menghubungi Ketua RT melalui WhatsApp: https://wa.me/{Config.RT_WHATSAPP_NUMBER}"
                         if Config.RT_WHATSAPP_NUMBER else f"Silakan hubungi {Config.RT_NAME} secara langsung."),
            'citation': None,
            'similarity_score': 0.0,
            'top_chunk_id': None,
            'escalation_whatsapp_url': f"https://wa.me/{Config.RT_WHATSAPP_NUMBER}" if Config.RT_WHATSAPP_NUMBER else None
        }

    q_stems = [simple_stem(w) for w in query_tokens]
    query_vec = Counter(query_tokens)

    # Ambil semua chunks dari database
    chunks = query_all("""
        SELECT c.chunk_id, c.knowledge_id, c.urutan_chunk, c.isi_chunk, c.kata_kunci,
               k.judul_dokumen, k.kategori
        FROM knowledge_chunks c
        JOIN knowledge_base k ON c.knowledge_id = k.knowledge_id
    """)

    best_chunk = None
    best_score = 0.0

    for chunk in chunks:
        # Gabungkan isi chunk dan kata kunci untuk representasi teks
        combined_text = f"{chunk['isi_chunk']} {chunk['kata_kunci'] or ''} {chunk['judul_dokumen']}"
        chunk_tokens = tokenize(combined_text)
        if not chunk_tokens:
            continue

        c_stems = [simple_stem(w) for w in chunk_tokens]

        # Lexical cosine similarity over term-frequency vectors.
        chunk_vec = Counter(chunk_tokens)
        cos_score = compute_cosine_similarity(query_vec, chunk_vec)

        # 2. Stemmed recall coverage of query words in chunk
        matched_stems = sum(
            1 for qs in q_stems 
            if any(qs == cs or (len(qs) >= 3 and qs in cs) or (len(cs) >= 3 and cs in qs) for cs in c_stems)
        )
        recall_score = matched_stems / len(q_stems) if q_stems else 0.0

        # Skor gabungan berbobot (mengutamakan cakupan query recall)
        final_score = max(cos_score, (recall_score * 0.75) + (cos_score * 0.25))
        final_score = min(final_score, 1.0)

        if final_score > best_score:
            best_score = final_score
            best_chunk = chunk

    threshold = Config.RAG_SIMILARITY_THRESHOLD

    if best_chunk and best_score >= threshold:
        # Grounded Answer
        clean_chunk_text = best_chunk['isi_chunk']
        answer_body = re.sub(r'^\d+\.\s*', '', clean_chunk_text)

        return {
            'is_escalated': False,
            'answer': f"Berdasarkan {best_chunk['judul_dokumen']}: {answer_body}",
            'citation': f"{best_chunk['judul_dokumen']} (Bagian {best_chunk['urutan_chunk']})",
            'similarity_score': round(best_score, 4),
            'top_chunk_id': best_chunk['chunk_id'],
            'escalation_whatsapp_url': None
        }
    else:
        # Fallback Eskalasi WhatsApp
        encoded_query = urllib.parse.quote(f"Halo {Config.RT_NAME}, saya warga {Config.RT_AREA} ingin menanyakan perihal: {query}")

        return {
            'is_escalated': True,
            'answer': (
                f"Maaf, informasi tersebut belum tercatat dalam basis data resmi {Config.RT_AREA}. "
                + ("Silakan hubungi Ketua RT melalui tombol WhatsApp di bawah."
                   if Config.RT_WHATSAPP_NUMBER
                   else "Silakan hubungi Ketua RT secara langsung.")
            ),
            'citation': None,
            'similarity_score': round(best_score, 4) if best_chunk else 0.0,
            'top_chunk_id': None,
            'escalation_whatsapp_url': (
                f"https://wa.me/{Config.RT_WHATSAPP_NUMBER}?text={encoded_query}"
                if Config.RT_WHATSAPP_NUMBER else None
            )
        }
