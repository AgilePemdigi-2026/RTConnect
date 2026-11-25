# TanyaRT Offline Chatbot & Evaluation Pipeline

## Overview
Offline RAG (Retrieval-Augmented Generation) research and evaluation pipeline for TanyaRT. This subsystem benchmarks semantic embeddings (`sentence-transformers`), lexical matching (`rank_bm25`), and rule-based heuristic scoring against Indonesian neighborhood administration knowledge chunks (`dataset/knowledgebase.jsonl`). It serves as the offline evaluation harness; the production runtime uses a lightweight, lexical-only service (`services/rag_service.py`) that does not depend on heavy ML libraries.

## Interface
- `TanyaRTService`: Core inference coordinator evaluating query intent, applying security/scope filters, and calculating hybrid scores.
  - `TanyaRTService.jawab(pertanyaan: str, dokumen_rt: list = None) -> dict`: Evaluates query against cached knowledge base and custom RT SOPs.
  - `get_service() -> TanyaRTService`: Singleton accessor with LRU cache.
  - `validasi_integritas_cache() -> bool`: Verifies hash integrity of dataset vs cached embeddings.
- `HybridRetriever`: Dual-engine search index combining dense embeddings and BM25 scoring.
  - `HybridRetriever.cari(pertanyaan: str, top_k: int = 5) -> list`: Retrieves top-ranked chunks with combined scores.
- `rules`: Indonesian linguistic heuristics and rule extraction.
  - `normalisasi(teks: str) -> str`: Lowercases and strips unwanted punctuation.
  - `tokenisasi(teks: str) -> list[str]`: Tokenizes query into stemmed/normalized terms.
  - `tokenisasi_bm25(teks: str) -> list[str]`: Generates BM25 tokens excluding stop words.
  - `semua_topik(teks: str) -> set`: Extracts administration topics (KTP, KK, Surat Pengantar, etc.).
  - `aksi_pertanyaan(teks: str) -> set`: Identifies action intents (buat, perpanjang, hilang, dll.).
  - `coverage(pertanyaan: str, dokumen: dict) -> float`: Calculates keyword overlap ratio.
- `api.py`: Optional standalone FastAPI server exposing `POST /v1/chat` and `GET /health` with Bearer token authentication.
- `evaluation.py`: Benchmark suite executing evaluation runs across ground-truth datasets.
- `embedding.py`: Generates dense vector representations using `paraphrase-multilingual-MiniLM-L12-v2`.

## Invariants
- Offline-only dependency boundary: This package requires `sentence-transformers`, `rank_bm25`, and `numpy` (listed in `backend/chatbot/requirements.txt`), which are intentionally excluded from the production API `requirements.txt`. Do NOT import `backend/chatbot` into production API routes.
- Cache reproducibility: Dense vector embeddings cached in `cache/embeddings.npy` must match the SHA256 digest of `dataset/knowledgebase.jsonl`.
- Authentication & Guardrails: Queries attempting to extract administrative secrets (PIN, OTP, password) must trigger an immediate deterministic `RAHASIA` rejection. Queries outside civil/RT scope must trigger `LUAR_CAKUPAN`.

## Side Effects
- File reads and writes: Reads dataset from `dataset/knowledgebase.jsonl`; reads and writes embedding cache arrays in `cache/`; writes benchmark metrics to `hasil_uji_*.csv` and `evaluation_results/`.
- Process memory: Loads deep learning models into CPU/CUDA memory when `embedding.py` or `api.py` is executed.

## Verification
- Run: `cd backend && python test_api.py`
- Offline evaluation test: `cd backend && python evaluate_runtime.py`
