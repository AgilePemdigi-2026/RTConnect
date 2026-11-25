# Migrasi LLM RTConnect ke Server Ollama

* **Author:** Dhafin-dev
* **Date:** 2026-11-25

## Overview

Inisiatif untuk mengalihkan pemrosesan kecerdasan buatan (Large Language Model) pada aplikasi administrasi RTConnect dari penyedia cloud eksternal (Google Gemini API dan OpenAI API) ke server mandiri berbasis **Ollama**. Tujuannya adalah mencapai kemandirian infrastruktur, privasi data lokal kependudukan, serta mengurangi ketergantungan kuota atau biaya API eksternal.

## Landasan Arsitektur Komponen AI RTConnect

Saat ini fitur AI di RTConnect terbagi ke dalam 3 komponen berbeda:

| Komponen | Berkas Sumber | Penyedia Saat Ini | Tugas & Karakteristik |
|---|---|---|---|
| **Asisten Pengisi Formulir (AI Fill)** | `backend/services/ai_fill_service.py` | Google Gemini API / OpenAI-Compatible | Menerima teks bebas dari warga, mengekstrak data demografi ke dalam format JSON ketat sesuai skema `applicant_data.py`. |
| **Sintesis TanyaRT (RAG)** | `backend/services/tanyart_llm_service.py` | Google Gemini API (`genai.Client`) | Mengambil teks konteks dari database, meminta LLM menyusun jawaban singkat (2-4 kalimat) santun dengan batas waktu maksimal 5 detik. |
| **Pencarian Semantik (Embedding)** | `backend/services/semantic_embedding_service.py` | OpenAI API (`text-embedding-3-small`) | Mengonversi teks pertanyaan menjadi vektor numerik 1536-dimensi untuk menghitung cosine similarity terhadap dokumen aturan RT. |

## Analisis Trade-Off & Kebutuhan Teknis

### 1. Topologi Jaringan & Kompatibilitas Endpoint
- Ollama secara bawaan mengekspos endpoint OpenAI-compatible pada rute `/v1/chat/completions` dan `/v1/embeddings`.
- Jika backend Flask berjalan di dalam Docker dan Ollama di host OS, target URL harus menggunakan `http://host.docker.internal:11434/v1`.
- Jika Ollama di server jaringan kampus/lokal lain, target URL adalah IP spesifik (misal `http://192.168.x.x:11434/v1`).

### 2. Kepatuhan Format JSON (Structured Outputs)
- Gemini mendukung jaminan struktur skema JSON tingkat API (`response_schema`).
- Model open-weight pada Ollama (seperti Llama-3.1, Qwen-2.5, Gemma-2) memerlukan prompt berdisiplin tinggi dan pembersihan regex output (menghilangkan wrapper markdown ` ```json `) agar tidak menggagalkan parsing data kependudukan.

### 3. Keterbatasan Hardware, Latensi, dan Concurrency
- Model lokal berukuran 7B hingga 14B parameter memerlukan VRAM GPU minimal 6 GB – 12 GB untuk inferensi cepat (< 3 detik).
- Jika dijalankan pada CPU, inferensi per kueri dapat memakan waktu 10 hingga 30 detik.
- Konkurensi multi-user pada satu server Ollama tanpa antrean terorkestrasi dapat menyebabkan penumpukan waktu tunggu yang memicu HTTP timeout pada klien Flutter.

## Status Pertanyaan Terbuka & Eksplorasi

1. **Cakupan Penggantian**: Menentukan apakah migrasi mencakup AI Form Fill saja, atau merombak TanyaRT synthesis dan semantic embedding sekaligus.
2. **Kesiapan Infrastruktur Server Ollama**: Mengetahui spesifikasi komputasi (GPU vs CPU), nama model yang di-deploy, serta alamat jaringan server.
3. **Penyelarasan SLA Kinerja**: Menilai apakah toleransi waktu tunggu 5 detik pada TanyaRT tetap dipertahankan atau disesuaikan.
4. **Strategi Kegagalan (Fallback)**: Menetapkan alur aksi ketika Ollama gagal merespon atau menghasilkan teks yang tidak dapat di-parse.
