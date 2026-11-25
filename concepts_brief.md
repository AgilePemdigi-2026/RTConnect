# Migrasi Penuh LLM RTConnect ke Server Kampus (Ollama)

* **Author:** Dhafin-dev
* **Date:** 2026-11-25

## Overview

Inisiatif untuk mengalihkan seluruh fungsionalitas kecerdasan buatan pada aplikasi administrasi RTConnect (asisten formulir persuratan dan chatbot TanyaRT) secara 100% ke server lokal/kampus berbasis **Ollama** (`qwen2.5:3b-instruct`), tanpa bergantung pada penyedia cloud berbayar (Google Gemini API atau OpenAI API). Pembaruan ini selaras dengan perubahan terbaru pada upstream repositori (`upstream/main`), yang menonaktifkan embedding eksternal dan menyediakan jalur endpoint lokal non-thinking.

## Analysis

### 1. Evaluasi Lensa Desain, Keamanan, & Basis Kode
- **Asimetri Autentikasi Cloudflare Access**:
  - `tanyart_llm_service.py` telah memvalidasi host kampus (`ollama.ebruar.my.id`) dan menginjeksikan header `CF-Access-Client-Id` serta `CF-Access-Client-Secret`.
  - `ai_fill_service.py` saat ini **belum** mengirimkan header Cloudflare Access pada `_call_openai_compatible`, sehingga pemanggilan formulir surat ke domain kampus akan langsung diblokir dengan `HTTP 403 Forbidden`.
- **Penghapusan Total Jejak Cloud (Zero-Cloud Invariant)**:
  - Jalur pemanggilan sekunder ke Google Gemini API pada `ai_fill_service.py` (`_call_gemini_api`) dinonaktifkan secara permanen.
  - Jika Ollama mengalami gangguan, sistem langsung beralih ke fallback deterministik lokal (data profil tersimpan dan template baku) tanpa mencoba melakukan *egress* jaringan ke cloud eksternal.
- **Kedaulatan & Kepatuhan Privasi (UU PDP No. 27/2022)**:
  - Dengan berjalannya seluruh inferensi di server kampus, cerita dan narasi pengajuan warga tidak pernah dikirim ke infrastruktur luar negeri.
- **Pengendalian Antrean & Konkurensi**:
  - `tanyart_llm_service.py` membatasi beban aktif dengan `BoundedSemaphore(2)`.
  - `ai_fill_service.py` perlu diselaraskan agar panggilan simultan dari banyak warga tidak membanjiri (*overload*) satu worker server kampus yang kapasitas VRAM-nya terbatas.

### 2. Inventive Contradictions & Resolusi Pola (TRIZ)
- **Kontradiksi 1: Model Ringan (3B) vs Ketepatan Ekstraksi Formulir**:
  - *Masalah*: Model 3B parameter memiliki kedalaman penalaran lebih rendah dibanding model komersial cloud, berisiko mengabaikan kutipan bukti (*grounding*) atau keliru memilih opsi enum surat.
  - *Resolusi (Prinsip TRIZ #10 - Preliminary Action)*: Mengandalkan `ai_guardrails.py` untuk memverifikasi teks kutipan secara deterministik. Jika ekstraksi model tidak lolos validasi, kolom otomatis diisi dari profil akun kependudukan warga yang tersimpan di database MySQL lokal (`sumber: 'tersimpan'`).
- **Kontradiksi 2: Fluktuasi Latensi Server Kampus vs Batas Waktu SLA Warga**:
  - *Masalah*: Server kampus dipakai bersama oleh civitas akademika sehingga latensi inferensi bisa melonjak di atas 5 detik saat jam sibuk.
  - *Resolusi (Prinsip TRIZ #24 - Intermediary & Asymmetric Budget)*: TanyaRT mematok batas waktu inferensi ketat maksimal 4.5 detik. Bila antrean macet, sistem seketika memotong proses LLM dan langsung mengembalikan potongan teks dokumen resmi yang terverifikasi tanpa memunculkan pesan error di layar warga.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  - Menyelaraskan konfigurasi environment `backend/.env` untuk server kampus (`LLM_BASE_URL`, `TANYART_LLM_BASE_URL`, `LLM_MODEL`, `CF_CLIENT_ID`, `CF_CLIENT_SECRET`).
  - Menambahkan dukungan header Cloudflare Access (`CF-Access-Client-Id` dan `CF-Access-Client-Secret`) pada `backend/services/ai_fill_service.py`.
  - Menghapus ketergantungan dan pemanggilan fallback ke Google Gemini API di seluruh alur persuratan.
  - Menyatukan konfigurasi dasar Ollama di `backend/config.py` agar tidak terjadi duplikasi setting yang membingungkan.
  - Memverifikasi fungsionalitas melalui suite uji TanyaRT (`python backend/test_tanyart_full.py`) dan latensi non-destruktif (`python backend/ukur_latensi_lengkap.py`).
* **Out-of-Scope Non-Goals:**
  - Menyediakan server Ollama baru (memanfaatkan infrastruktur kampus yang sudah berjalan).
  - Mengaktifkan model berukuran besar (>7B) atau model bertipe penalaran (*reasoning*) seperti Qwen-Thinking/DeepSeek-R1 yang membutuhkan waktu >20 detik per kueri.
  - Mengaktifkan kembali model embedding eksternal (TanyaRT tetap beroperasi 100% pada pencarian leksikal deterministik).

## Alternatives Weighed

- **Alternatif 1: Model Campuran / Hybrid (Ollama Utama + Gemini Cadangan)**
  - *Alasan Ditolak*: Pengguna secara tegas memilih opsi *Full gunakan Ollama* (100% on-premise) untuk menjamin kemandirian data kependudukan dan memutus ketergantungan kuota cloud.
- **Alternatif 2: Model Besar 14B / 32B**
  - *Alasan Ditolak*: Spesifikasi server kampus tidak diketahui. Model di atas 7B rentan memicu OOM (*Out of Memory*) dan latensi tinggi yang melanggar SLA batas waktu respon.
- **Alternatif 3: Embedding Vektor Lokal di Ollama (bge-m3 / nomic-embed)**
  - *Alasan Ditolak*: Evaluasi upstream membuktikan retrieval leksikal (TF-IDF + Indonesian stemming) telah lulus 100% pengujian fungsionalitas tanpa beban tambahan kueri vektor ke server kampus.

## Key Decisions & Staging for Next Steps

1. **Sinkronisasi Kode**: `git merge upstream/main` telah berhasil digabungkan tanpa konflik.
2. **Implementasi Konfigurasi Server Kampus**:
   - Menyetel variabel environment `backend/.env` dengan IP server Ollama kampus `http://192.168.88.237:11434/v1` dan model `qwen2.5:3b-instruct`.
   - Memperbarui `backend/config.py` agar menyelaraskan `TANYART_LLM_BASE_URL` dan `TANYART_LLM_MODEL` dengan fallback otomatis ke `LLM_BASE_URL`.
   - Memperbarui `backend/services/ai_fill_service.py` dengan normalisasi endpoint `/v1/chat/completions`, dukungan Cloudflare Access (`CF_CLIENT_ID`/`CF_CLIENT_SECRET`), dan penonaktifan total jalur pemanggilan eksternal Gemini (100% on-premise).
   - Memperbarui `backend/services/tanyart_llm_service.py` dengan fallback terpadu ke `Config.LLM_BASE_URL` serta validasi whitelist endpoint `192.168.88.237`.
3. **Hasil Verifikasi Uji**:
   - Seluruh suite uji `backend/test_tanyart_full.py` lulus 100% (26/26 kasus regresi retrieval, strict grounding, anti-injeksi, dan simulasi kontrak HTTP Ollama).
