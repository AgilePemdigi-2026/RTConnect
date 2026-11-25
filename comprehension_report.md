# Comprehension Test Audit Report: `docs/designs/migrasi_llm_ollama.md`

### What this proposes
Dokumen ini mengusulkan migrasi 100% fungsionalitas kecerdasan buatan pada sistem RTConnect—khususnya modul asisten pengisian formulir surat warga (`ai_fill_service`) dan modul asisten tanya-jawab regulasi lingkungan TanyaRT (`tanyart_llm_service`)—dari penyedia cloud pihak ketiga (Google Gemini API dan OpenAI API) ke server lokal mandiri berbasis Ollama di jaringan kampus menggunakan model `qwen2.5:3b-instruct`. Seluruh panggilan keluar (*outbound egress*) ke cloud AI eksternal dieliminasi demi kepatuhan terhadap UU Perlindungan Data Pribadi (UU PDP No. 27/2022) serta penghapusan biaya kuota API. Sistem menetapkan mekanisme pembatasan konkurensi (maksimal 2 *thread* simultan via `BoundedSemaphore`), dukungan autentikasi Cloudflare Access untuk akses publik, dan fallback deterministik lokal (data profil kependudukan tersimpan untuk formulir surat dan kutipan verbatim regulasi untuk TanyaRT) saat server Ollama mengalami timeout atau kegagalan.

### How the existing system works, per this document
Sesuai uraian dokumen ini, arsitektur AI RTConnect sebelumnya bersifat terfragmentasi di mana asisten formulir surat baru mendukung server lokal secara parsial dengan fallback ke Google Gemini, modul chatbot TanyaRT terkunci mati pada SDK Gemini, dan modul pencarian semantik mengandalkan OpenAI API (`text-embedding-3-small`). Ketergantungan ini mengekspos narasi cerita dan data kependudukan warga ke server cloud luar negeri yang berisiko terhadap kepatuhan hukum dan insiden kehabisan kuota (HTTP 429). Di sisi lain, sistem telah memiliki modul retrieval leksikal deterministik (TF-IDF + Cosine Similarity + Stemming Bahasa Indonesia) pada `backend/services/rag_service.py` yang terbukti lulus uji regresi 26 kasus tanpa membutuhkan embedding vektor eksternal.

---

### Audit Findings

#### 1. 🔴 Blocker: Ambiguitas Arsitektur Database & Kontradiksi Kedaulatan Data (PostgreSQL / Supabase)
* **Affected Scope**: Section "Non-Goals" (Line 36), Section "Technical Plan" Mermaid Diagram (Lines 94, 123), Section "Invarian 2" (Line 185).
* **Discrepancy Description & Rationale**:
  Dokumen secara berulang menyebut database sistem sebagai gabungan `"PostgreSQL / Supabase"` (misalnya pada baris 36: *"Mengubah skema database PostgreSQL / Supabase yang sudah berjalan"*, baris 94: `Local_DB[("Database PostgreSQL / Supabase")]`, dan baris 185: *"snapshot profil kependudukan di Supabase"`).
  Bagi insinyur baru yang membaca dokumen ini:
  1. Istilah ini ambigu karena Supabase pada umumnya dikenal sebagai layanan cloud *Backend-as-a-Service* (BaaS) pihak ketiga. Jika profil kependudukan warga disimpan di cloud Supabase, hal ini bertentangan langsung (*contradiction*) dengan tujuan utama dokumen yaitu "Kedaulatan Data Lokal 100% On-Premise" dan "Zero Outbound Leak". Jika Supabase yang dimaksud adalah *self-hosted* lokal, hal tersebut sama sekali tidak dijelaskan.
  2. Dokumen arsitektur repositori umum (`AGENTS.md`) mendefinisikan backend menggunakan skema/migrasi MySQL. Dokumen desain ini sama sekali tidak menjelaskan konteks transisi atau hubungan antara MySQL, PostgreSQL, dan Supabase, sehingga pembaca baru tidak dapat memahami di mana data warga sebenarnya berada dan bagaimana fallback `Local_DB` beroperasi.

#### 2. 🔴 Blocker: Kontradiksi Langsung Antara Invarian Zero-Cloud dan Rencana Implementasi Kode
* **Affected Scope**: Section "4. Kebijakan Zero-Cloud & Fail-Safe Invariants" (Line 184) vs Section "Target Files to Create/Modify - Butir 4 (`ai_fill_service.py`)" (Lines 268-277).
* **Discrepancy Description & Rationale**:
  Pada baris 184, dokumen menetapkan kontrak teknis yang mutlak:
  > *"Invarian 1 (Zero Outbound Leak): Tidak ada modul backend yang mengimpor atau memanggil `google.genai` Client maupun endpoint `api.openai.com`. Seluruh pustaka cloud AI dinonaktifkan dalam alur kerja runtime."*
  
  Namun, pada Rencana Implementasi Rinci (baris 268-277), modifikasi pada `ai_fill_service.py` hanya mengubah fungsi `_call_openai_compatible` dan `_call_gemini` untuk mematikan fallback runtime. Rencana tersebut **tidak** menginstruksikan penghapusan baris impor (`from google import genai`), tetap mempertahankan fungsi `_call_gemini_api()`, dan mempertahankan penamaan fungsi `_call_gemini`.
  Insinyur baru yang membaca Technical Plan akan mengira seluruh modul bersih dari dependensi `google.genai`, namun implementasinya tetap mengimpor pustaka tersebut. Terdapat ketidaksinkronan nyata antara invarian arsitektur dan rincian modifikasi kode.

#### 3. 🟡 Major: Alur Eksekusi Tidak Logis pada Diagram Arsitektur Komponen
* **Affected Scope**: Section "1. Arsitektur Komponen & Diagram Alur Data" (Lines 81-86, 103-107).
* **Discrepancy Description & Rationale**:
  Diagram Mermaid memodelkan alur persuratan sebagai berikut:
  `Route_Letter --> Masker --> Guard_SOP --> Service_Fill --> Ollama_Direct`.
  Diagram ini menggambarkan bahwa `Guard_SOP` ("Verifikasi SOP & Guardrails Anti-Halusinasi") dieksekusi **sebelum** `Service_Fill` dan **sebelum** kueri dikirim ke `Ollama_Direct`.
  Secara logika rekayasa perangkat lunak, verifikasi anti-halusinasi dan kepatuhan SOP terhadap isian surat (tujuan, keperluan, bukti kutipan) hanya dapat mengevaluasi hasil ekstraksi yang **dihasilkan oleh model AI**. Verifikasi SOP tidak dapat dilakukan mendahului pemanggilan LLM karena datanya belum diekstrak. Pada kode riil (`ai_fill_service.py`), `suggest_application` memanggil model terlebih dahulu, baru kemudian menjalankan guardrail `check_sop` dan pembersihan hasil. Diagram ini membingungkan alur logika bagi pengembang baru.

#### 4. 🟡 Major: Kerancuan Topologi Jaringan & Batas Klien vs. Backend pada Cloudflare Access
* **Affected Scope**: Section "Open Questions" (Lines 40-41), Section "1. Arsitektur Komponen" (Lines 97-101, 114-118), dan Section "2. Protokol Komunikasi" (Lines 139-140).
* **Discrepancy Description & Rationale**:
  Pada Open Question 1 (baris 40), dokumen mempertanyakan:
  > *"Bagaimana stabilitas koneksi IP lokal 192.168.88.237 ketika aplikasi diakses di luar jaringan WiFi kampus (apakah diperlukan mekanisme auto-switch ke domain Cloudflare ollama.ebruar.my.id)?"*
  
  Sementara itu, pada diagram Mermaid (baris 114-118), garis putus-putus fallback (`Fallback Cloudflare Headers --> Ollama_CF`) digambarkan seolah-olah arsitektur auto-fallback sudah ada.
  Hal ini menimbulkan kerancuan ganda bagi pembaca:
  1. **Kerancuan Batas Sistem**: Klien mobile Flutter hanya berkomunikasi dengan backend Flask (`/api/v1/letters/ai-fill`), bukan langsung ke Ollama. Ketercapaian IP `192.168.88.237` adalah relasi antara server backend Flask dan server Ollama. Dokumen tidak menjelaskan apakah backend Flask di-hosting di dalam jaringan kampus atau di laptop pengembang lokal.
  2. **Hand-waving Failover**: Dokumen menampilkan rute fallback ke Cloudflare Access di diagram, namun tidak mendefinisikan mekanisme peralihannya pada kode (apakah dinamis saat timeout IP lokal terjadi, atau harus ganti manual via `.env`). Hal ini dibiarkan menggantung antara status "sudah dirancang" atau "masih pertanyaan terbuka".

#### 5. 🟢 Nit: Singkatan Domain Spesifik dan Penomoran Regulasi Tanpa Definisi/Tautan
* **Affected Scope**: Lines 27, 48, 173, 186, 217, 221, 316.
* **Discrepancy Description & Rationale**:
  Dokumen menggunakan singkatan dan istilah internal tanpa penjelasan singkat (*inline definition*) atau pranala dokumen:
  - `SLA NFR 5.1`: Dirujuk berkali-kali sebagai standar latensi (< 5.0 detik), tetapi dokumen SRS atau PRD asal penamaan NFR 5.1 ini tidak ditautkan atau didefinisikan.
  - `SKD`: Muncul di CUJ 1 (baris 48: *"mengekstrak jenis surat SKD"*) tanpa kepanjangan (*Surat Keterangan Domisili*) atau tautan ke daftar enum jenis surat resmi.
  - `Pedoman RT (RTC-014)`: Disebutkan di baris 186 sebagai contoh rujukan tanpa penjelasan bahwa `RTC-XXX` adalah format identifier potongan dokumen offline pada `knowledge_chunks`.
  - `NIK/KK`: Digunakan di baris 217 tanpa kepanjangan (*Nomor Induk Kependudukan / Kartu Keluarga*).

#### 6. 🟢 Nit: Asimetri Konvensi Penamaan Variabel Konfigurasi Batas Waktu (Timeout)
* **Affected Scope**: Section "Target Files to Create/Modify" (Lines 244, 247) dan Section "2. Protokol Komunikasi" (Lines 155, 173).
* **Discrepancy Description & Rationale**:
  Terdapat inkonsistensi pola penamaan variabel lingkungan:
  - Untuk asisten persuratan: `LLM_TIMEOUT_SECONDS=15` (menggunakan sufiks satuan `_SECONDS` dan integer).
  - Untuk TanyaRT: `TANYART_LLM_TIMEOUT=5.0` (tanpa sufiks satuan `_SECONDS` dan float).
  Meskipun kode dapat membaca keduanya, dokumen tidak menjelaskan apakah `TANYART_LLM_TIMEOUT` mewarisi `LLM_TIMEOUT_SECONDS` jika tidak disetel, menimbulkan beban kognitif (*cognitive friction*) bagi pengembang baru saat mengonfigurasi `.env`.

#### 7. 🟢 Nit: Ketidakjelasan Jalur Berkas (*Path*) untuk `concepts_brief.md`
* **Affected Scope**: Section "Target Files to Create/Modify - Butir 7" (Lines 294-297).
* **Discrepancy Description & Rationale**:
  Berkas target hanya ditulis `concepts_brief.md` tanpa kejelasan path direktori (apakah di root repositori atau di dalam folder `docs/`). Sementara itu, semua berkas target lainnya secara eksplisit menyertakan path relatif lengkap (misal: `backend/config.py`, `backend/services/ai_fill_service.py`). Pengembang baru harus mencari manual letak berkas tersebut.
