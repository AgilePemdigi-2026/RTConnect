"""Layanan Embedding Semantik TanyaRT (SRS REQ-3, REQ-7).

SRS mewajibkan pencarian semantik menggunakan representasi vektor
dengan model text-embedding-3-small dan cosine similarity (ambang 0,70).

Modul ini menyediakan:
- generate_embedding(text): memanggil API embedding resmi (OpenAI text-embedding-3-small).
- cosine_similarity(vec1, vec2): menghitung cosine similarity murni antara dua vektor numerik.
- semantic_search(query_vec, chunks, threshold=0.70): mencari chunk dengan kemiripan vektor tertinggi.
- Penanganan transparan bila OPENAI_API_KEY belum dikonfigurasi di environment.
"""

import json
import logging
import math
import os
import urllib.error
import urllib.request
from typing import Any

from config import Config

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 1536  # text-embedding-3-small standar


class EmbeddingServiceUnavailableError(Exception):
    """Dilempar bila layanan embedding tidak tersedia atau gagal dipanggil."""


def is_embedding_configured() -> bool:
    """True jika OPENAI_API_KEY / EMBEDDING_API_KEY telah diisi."""
    return bool(Config.EMBEDDING_API_KEY or Config.OPENAI_API_KEY)


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
    """Menghasilkan vektor embedding untuk teks menggunakan text-embedding-3-small.

    Raise EmbeddingServiceUnavailableError jika API key belum ada, koneksi gagal,
    atau waktu panggilan melebihi batas waktu (timeout).
    """
    api_key = Config.EMBEDDING_API_KEY or Config.OPENAI_API_KEY
    if not api_key:
        raise EmbeddingServiceUnavailableError(
            "OPENAI_API_KEY atau EMBEDDING_API_KEY belum dikonfigurasi di environment "
            "untuk model text-embedding-3-small."
        )

    clean_text = text.strip().replace("\n", " ")
    if not clean_text:
        return [0.0] * EMBEDDING_DIMENSION

    payload = {
        "model": Config.EMBEDDING_MODEL or "text-embedding-3-small",
        "input": clean_text,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            vector = data["data"][0]["embedding"]
            return [float(x) for x in vector]
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise EmbeddingServiceUnavailableError(
            f"OpenAI Embedding API error HTTP {err.code}: {body}"
        ) from err
    except Exception as err:
        raise EmbeddingServiceUnavailableError(
            f"Gagal memanggil OpenAI Embedding API: {type(err).__name__}: {err}"
        ) from err


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
