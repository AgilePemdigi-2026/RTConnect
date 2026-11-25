"""TanyaRT vector utilities. Hosted embeddings are disabled in local mode."""
import math
from typing import Any
import json

EMBEDDING_DIMENSION = 1536  # text-embedding-3-small standar


class EmbeddingServiceUnavailableError(Exception):
    """Dilempar bila layanan embedding tidak tersedia atau gagal dipanggil."""


def is_embedding_configured() -> bool:
    return False


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Menghitung cosine similarity numerik murni antara dua vektor float.

    Kembalian berada dalam rentang [-1.0, 1.0]. Bila salah satu vektor bernilai nol,
    mengembalikan 0.0.
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def generate_embedding(text: str, timeout: float = 5.0) -> list[float]:
    raise EmbeddingServiceUnavailableError("Embedding lokal belum dikonfigurasi.")


def search_semantic_chunks(
    query_vector: list[float],
    chunks: list[dict[str, Any]],
    threshold: float = 0.70,
) -> tuple[dict[str, Any] | None, float, list[dict[str, Any]]]:
    """Cari potongan dokumen berdasarkan cosine similarity embedding tertinggi.

    Hanya potongan dokumen yang memiliki 'embedding_vector' (bertipe list float)
    yang dapat dievaluasi semantik.

    Mengembalikan (best_chunk, best_score, all_ranked_results).
    """
    if not query_vector:
        return None, 0.0, []

    ranked = []
    for chunk in chunks:
        vec = chunk.get("embedding_vector")
        if not vec:
            continue
        if isinstance(vec, str):
            try:
                vec = json.loads(vec)
            except Exception:
                continue
        if not isinstance(vec, list) or len(vec) != len(query_vector):
            continue

        sim = cosine_similarity(query_vector, vec)
        ranked.append({
            "chunk": chunk,
            "cosine_score": round(sim, 4),
        })

    if not ranked:
        return None, 0.0, []

    ranked.sort(key=lambda x: x["cosine_score"], reverse=True)
    best = ranked[0]
    best_chunk = best["chunk"] if best["cosine_score"] >= threshold else None
    return best_chunk, best["cosine_score"], ranked
