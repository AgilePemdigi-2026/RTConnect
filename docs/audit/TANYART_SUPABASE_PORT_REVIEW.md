# TANYART SUPABASE PORT REVIEW (WORKTREE INTEGRASI — BELUM COMMIT)

Tanggal: 12 November 2026.
Worktree: `../RTConnect-integration`, branch `feat/supabase-tanyart-integration`, basis `origin/main` (`deb7f36`).
Putaran verifikasi integrasi database: 12 November 2026 (tanpa perubahan kode; tanpa pola/tuning baru).
Worktree branch aktif `feat/chatbot-improvement` (`a68f04b`) tidak disentuh. Tidak ada akses database produksi, tidak ada commit/push, tidak ada merge/rebase, blind V8 tidak dibuka, tidak ada template WhatsApp baru.

## 1. Inventarisasi sumber perubahan

### Commit chatbot yang relevan (branch aktif)
- `a68f04b` — `training chatbot v7`: menambah `backend/chatbot/dataset_v7_cases.py` (1141 baris), hasil uji (`hasil_uji_runtime.csv`, `hasil_tahap6_blind_test.json`), dan penyesuaian `evaluate_runtime.py` + `services/chatbot_rules.py` + `services/rag_service.py`.
- `6e68cb8`, `fcb1469` — hanya perubahan `README.md` (logo), tidak relevan untuk port fungsional.

### Perubahan lokal belum di-commit yang dipindahkan secara selektif
Dari worktree aktif (`git status`): `chatbot_rules.py`, `rag_service.py`, `chatbot_routes.py` (dimodifikasi), `sanitize_historical_chat.py` (file baru, untracked), `docs/`, `scripts/` (artefak audit, tidak dipindahkan).

### File baru yang relevan
- `backend/database/sanitize_historical_chat.py` — skrip sanitasi historis MySQL-era; **tidak dipindahkan** ke branch integrasi (dicatat sebagai pekerjaan terbuka, lihat bagian 6).

## 2. Batas transaksi endpoint query (/api/v1/chatbot/query)

Struktur aktual di worktree integrasi (`backend/routes/chatbot_routes.py:34-92`):

1. `INSERT INTO chatsession ... RETURNING` — di luar transaksi (baris 36).
2. Validasi `session_id` + sanitasi pre-persistence pesan warga — di luar transaksi (baris 40-57).
3. `INSERT INTO chatmessage (pengirim='warga')` — di luar transaksi (baris 60-63).
4. `search_knowledge_base(query_text)` — komputasi retrieval murni, tanpa tulis DB.
5. Blok `with transaction() as cur:` — mencakup `INSERT chatmessage` balasan AI + `INSERT retrievallog` (opsional) + `UPDATE chatsession SET status='dieskalasi'` (bila eskalasi) + `add_notification(...)` (bila ada `rt_id`).

### 2.1 Koreksi klaim sebelumnya: tidak ada dasar SRS untuk respons HTTP 500

Pernyataan pada versi sebelumnya bahwa "Gherkin mewajibkan sesi dan pesan tercatat untuk setiap request valid HTTP 200" diralat. Verifikasi ulang terhadap `backend/features/sprint1/issue_11_chatbot_tanyart.gherkin` (5 skenario: masa berlaku surat, pencatatan riwayat umum, eskalasi turnamen, daftar sesi, detail pesan) menunjukkan:

- Tidak ada skenario yang mencakup **kegagalan retrieval** (`search_knowledge_base` melempar exception).
- Tidak ada skenario yang mencakup **kegagalan tulis AI/notifikasi di tengah transaksi**.
- Tidak ada ekspektasi status HTTP 500 di seluruh file Gherkin sprint-1 (kegagalan yang diuji hanya validasi input 4xx seperti NIK/email duplikat dan password salah).

**Keputusan yang benar: perilaku request gagal adalah KEPUTUSAN TERBUKA (undecided)**, bukan "diwajibkan SRS". Tidak ada dasar SRS untuk mengklaim pesan warga *harus* tetap tersimpan ketika request berakhir 500, dan tidak ada dasar untuk mengklaim sebaliknya.

### 2.2 Keadaan database aktual pada tiap titik kegagalan (hasil reproduksi perilaku kode)

Uji dilakukan dengan membaca urutan statement di handler, tanpa database live (mock terisolasi setara urutan kode):

| Titik kegagalan | Sesi baru | Sesi lama (sudah ada) |
|---|---|---|
| `search_knowledge_base` melempar (sebelum blok transaksi) | Sesi `berlangsung` sudah dibuat + **pesan warga (tersanitasi) sudah tersimpan**, tanpa balasan AI, tanpa notifikasi, tanpa perubahan status | Sama: validasi kepemilikan lolos, **pesan warga baru tersimpan**, lalu retrieval gagal — tidak ada balasan AI/notifikasi/status baru |
| `cur.execute(INSERT chatmessage AI)` gagal di dalam transaksi | Sesi + pesan warga sudah tersimpan; **rollback** membatalkan balasan AI, retrievallog, update status, dan notifikasi | Sama: pesan warga baru tetap tersimpan; blok AI/status/notif di-rollback penuh |
| `add_notification` gagal di dalam transaksi | Sesi + pesan warga tersimpan; balasan AI ikut ter-rollback (tidak ada balasan yatim) | Sama |

**Catatan penting perbedaan mock vs Postgres asli:** hasil di atas adalah hasil pembacaan urutan kode + reproduksi mock terisolasi (`mock_db_*`), BUKAN bukti rollback PostgreSQL live. Klaim rollback transaksional pada Postgres disposable tetap **SKIP** (lihat Bagian 5) sampai failure injection dijalankan terhadap database uji terisolasi.

### 2.3 Keputusan batas transaksi (dipertahankan, dengan alasan yang dikoreksi)

Batas transaksi saat ini dipertahankan **bukan** karena "SRS mewajibkan pesan tersimpan saat 500" (klaim tersebut dicabut), melainkan karena:

1. Memindahkan pembuatan sesi + pesan warga ke *dalam* transaksi akan mengubah perilaku pembacaan riwayat yang sudah diuji (pesan warga hilang dari riwayat bila retrieval gagal padahal pertanyaan valid dan tersanitasi dengan benar).
2. Mempersempit transaksi (mis. hanya insert AI tanpa notifikasi/status) justru menciptakan risiko balasan yatim dan status/notifikasi tidak konsisten.
3. Perubahan batas transaksi tanpa dasar SRS adalah perubahan perilaku yang tidak diminta tugas ini.

Jika keputusan produk di masa depan menghendaki semantik "semua-atau-tidak-sama-sekali" untuk satu request chatbot, maka seluruh alur (sesi + pesan warga + retrieval + balasan + status + notifikasi) perlu dibungkus satu transaksi dan diuji ulang — dicatat sebagai **pekerjaan terbuka**, bukan perubahan diam-diam.

## 3. Regresi sanitasi frasa pemulihan — reproduksi temuan gagal + perbaikan terverifikasi

### 3.1 Baseline SEBELUM perbaikan (hasil aktual, dua tahap)

Kasus F1 dikonfirmasi gagal dalam dua tahap:

1. **HEAD pra-port** (`deb7f36`, sebelum port sanitasi): fungsi `contains_raw_ssh_or_seed_phrase` / `is_sensitive_credential_for_storage` **belum ada** — verifikasi `git show HEAD:... | grep -c` mengembalikan 0. Kredensial seed phrase lolos dan akan tersimpan mentah (implisit False). Ini baseline pra-port yang sebenarnya.
2. **Patch-awal port** (connector generik tanpa pola `cadangan`, daftar fungsi masih memuat kata benda domain): reproduksi dengan logika identik menghasilkan **False** pada kasus F1-baru. Perintah: skrip inline yang memakai regex connector + himpunan kata fungsi patch-awal.

| Kasus | Input sintetis | Harapan | HEAD (pra-port) | Patch-awal | Status temuan |
|---|---|---|---|---|---|
| plain spasi | `seed phrase: abandon ability able ...` (12 kata) | redact (True) | tidak ada fungsi (lolos mentah) | True | PASS (port menutup celah) |
| koma | `seed phrase: abandon, ability, ...` | redact (True) | tidak ada fungsi | True | PASS |
| edu lalu payload | `Apa itu ...? Recovery phrase saya: <12 kata>` | redact (True) | tidak ada fungsi | True | PASS |
| preposisi konteks | `seed phrase untuk dompet saya: <12 kata>` | redact (True) | tidak ada fungsi | True | PASS |
| **F1-baru: pengantar panjang** | `seed phrase: ini adalah cadangan untuk dompet digital saya, <12 kata>` | redact (True) | tidak ada fungsi | **False** | **FAIL (temuan terkonfirmasi)** |
| kontrol edukasi ID | kalimat tanya/edukatif ID tanpa payload | lolos (False) | n/a | False | PASS |
| kontrol edukasi EN | kalimat edukatif EN tanpa payload | lolos (False) | n/a | False | PASS |

Akar masalah (umum, bukan hardcode kalimat): setelah indikator `seed phrase`, pembersih connector patch-awal tidak mencakup kata `cadangan` dan varian frasa kepemilikan `dompet digital (saya)`. Sisa pengantar masuk ke jendela 12 kata pertama bersama payload, sehingga penghitung kata fungsi menemukan `untuk` + `dompet` + `digital` + `saya` = memenuhi ambang `>= 2` dan kandidat dibuang sebagai "kalimat natural". Verifikasi langsung: `re.sub` patch-awal pada `after` menyisakan `'cadangan untuk dompet digital saya, abandon ...'`; verifikasi tahap kedua (setelah `cadangan` ditambah tetapi pola `digital` belum umum) masih menyisakan `'digital saya, abandon ...'` — keduanya memicu false negative lewat jalur yang sama. Perbaikan final menggeneralkan pola domain (`dompet(?:\s+digital)?`, `digital(?:\s+saya)?`, dst.) sehingga seluruh varian kepemilikan terbuang sebelum evaluasi jendela..

### 3.2 Perbaikan berbasis struktur payload (bukan pengecualian kalimat contoh)

File diubah: `backend/services/chatbot_rules.py` (hanya blok `SENTENCE_FUNCTION_WORDS` + docstring + regex connector).

Prinsip umum yang diterapkan:
1. Kata benda domain (`dompet`, `digital`, `kripto`, `crypto`, `akun`, `wallet`) **dikeluarkan** dari daftar kata fungsi kalimat (pola connector digeneralkan menjadi `dompet(?:\s+digital)?`, `digital(?:\s+saya)?`, `kripto/crypto(?:\s+saya)?` agar varian apa pun terbuang sebelum evaluasi jendela) — kata-kata ini dapat muncul sah di dalam frasa kepemilikan pengantar payload ("untuk dompet saya", "dompet digital saya") dan tidak boleh dihitung sebagai bukti kalimat natural. Sebagai gantinya ditambahkan kata kerja/kata benda naratif yang tidak mungkin menjadi bagian payload acak (`jaga`, `lindungi`, `cadangan`, `mencadangkan`, dst.).
2. Daftar connector pengantar diperluas dengan pola `cadangan(?:\s+untuk)?` sehingga `ini adalah cadangan untuk dompet digital saya,` terbuang penuh sebelum jendela 12 kata dievaluasi — berlaku umum untuk varian (`cadangan saya`, `cadangan untuk wallet saya`, dst.), bukan hanya kalimat contoh.
3. Iterasi `finditer` atas SEMUA indikator + filter `>= 2 kata fungsi` dipertahankan sebagai lapisan kedua.

### 3.3 Hasil SESUDAH perbaikan (perintah dan output aktual, bukti CSV tersimpan)

Perintah yang sama dijalankan ulang setelah patch, ditambah variasi pengantar dan kontrol edukatif:

| Kasus | Input sintetis | Harapan | Aktual (sesudah) | Status |
|---|---|---|---|---|
| plain spasi | `seed phrase: <12 kata>` | redact | True | PASS |
| koma | `seed phrase: <12 kata koma>` | redact | True | PASS |
| edu lalu payload | `... Recovery phrase saya: <12 kata>` | redact | True | PASS |
| preposisi konteks | `seed phrase untuk dompet saya: <12 kata>` | redact | True | PASS |
| **F1-baru pengantar panjang** | `seed phrase: ini adalah cadangan untuk dompet digital saya, <12 kata>` | redact | **True** | **PASS (diperbaiki)** |
| variasi pengantar cadangan | `seed phrase ini cadangan saya: <12 kata>` | redact | True | PASS |
| variasi untuk wallet | `recovery phrase untuk wallet saya <12 kata>` | redact | True | PASS |
| variasi digital | `seed phrase untuk dompet digital saya <12 kata>` | redact | True | PASS |
| variasi kripto | `recovery phrase untuk akun kripto saya: <12 kata>` | redact | True | PASS |
| kontrol nomor urut | `Kunci pemulihan: 1. apple ... 12. lemon` | redact | True | PASS |
| kontrol tanda hubung | `frasa pemulihan: abandon-ability-...-account` | redact | True | PASS |
| kontrol edukasi ID | kalimat tanya/edukatif ID tanpa payload | lolos | False | PASS |
| kontrol edukasi EN | kalimat edukatif EN tanpa payload | lolos | False | PASS |
| kontrol pertanyaan umum | `Bagaimana cara menjaga keamanan akun saya?` | lolos | False | PASS |
| kontrol KTP | `Bagaimana mengurus KTP yang hilang di Surabaya?` | lolos | False | PASS |

Total: **15/15 PASS** sesudah perbaikan final (sebelumnya: HEAD pra-port tidak ada fungsi; patch-awal 1 FAIL terkonfirmasi pada F1-baru). Bukti terstruktur: `docs/audit/bukti/sanitasi_seedphrase_2026-11-12.csv` (15 baris: 11 redact True + 4 kontrol False). Tidak ada perubahan threshold, bobot ranking, label, atau dataset.

### 3.4 Temuan lanjutan F2: pengantar naratif panjang sebelum payload (temuan Codex)

Kasus baru (payload sintetis 12 kata yang sama seperti F1): `Seed phrase saya catat dengan aman untuk keadaan darurat: <12 kata>` — fungsi `is_sensitive_credential_for_storage()` mengembalikan **False** (temuan Codex, seharusnya **True**). Baseline direproduksi di worktree ini sebelum patch F2:

| Kasus | Harapan | Sebelum (aktual) | Status |
|---|---|---|---|
| F2-tugas: `Seed phrase saya catat dengan aman untuk keadaan darurat: <12 kata>` | True | False | **FAIL (temuan terkonfirmasi)** |
| variasi susunan: `seed phrase untuk keadaan darurat saya catat dengan aman: <12 kata>` | True | False | FAIL |
| variasi catat-simpan: `seed phrase saya simpan baik-baik untuk jaga-jaga: <12 kata>` | True | False | FAIL |
| variasi pegang-darurat: `recovery phrase tolong pegang baik-baik untuk kondisi darurat <12 kata>` | True | True | PASS (terselamatkan posisi) |
| kontrol edukatif-mirip ID (tanpa payload) | False | False | PASS |
| kontrol edukatif-mirip EN (tanpa payload) | False | False | PASS |

Akar masalah (umum, bukan hardcode kalimat): pengantar naratif `saya catat dengan aman untuk keadaan darurat` TIDAK tercakup pola connector (bukan frasa kepemilikan), sehingga masuk ke jendela 12 kata pertama bersama 7 kata payload. Kata `dengan` + `untuk` sudah memenuhi ambang `>= 2 kata fungsi` → kandidat dibuang. Menambah kata (`catat`, `aman`, `darurat`, ...) ke daftar fungsi justru memperburuk semua kasus sejenis — jadi perbaikan yang benar adalah struktural: **jendela geser** yang menilai setiap rentang 12 kata berurutan setelah indikator. Payload 12 kata murni (tanpa kata fungsi) selalu lolos di salah satu posisi geser; kalimat edukatif tanpa payload tetap ditolak karena TIDAK ADA rentang 12 kata bersih di seluruh teks.

Perbaikan (`backend/services/chatbot_rules.py`, fungsi `contains_raw_ssh_or_seed_phrase` + docstring langkah 3): ganti evaluasi jendela tunggal `words[:12]` menjadi loop `words[start:start+12]`; kata naratif pengantar (`catat/mencatat/simpan/menyimpan/tulis/menulis/pegang/aman/darurat/keadaan`) ditambahkan ke `SENTENCE_FUNCTION_WORDS` sebagai lapisan kedua agar kalimat edukatif panjang tanpa payload tetap False. Hasil sesudah: **F2-set 6/6 PASS, F1-set lama tetap 15/15 PASS — total 21/21 PASS**. Bukti: `docs/audit/bukti/sanitasi_seedphrase_2026-11-12.csv` (21 baris: 15 redact True + 6 kontrol False).

## 4. Koreksi inventarisasi skrip sanitasi historis

Koreksi terhadap laporan sebelumnya: `backend/database/sanitize_historical_chat.py` **belum ada di worktree integrasi** (hasil `ls` negatif, grep negatif). File tersebut hanya ada sebagai untracked file di worktree branch aktif. Statusnya dicatat sebagai **pekerjaan terbuka**, bukan bagian dari port ini — sesuai batasan agar tidak memindahkan runner/tools MySQL-era tanpa adaptasi skema Supabase (`chatmessage`/`retrievallog`/`notifikasi` baru + `transaction()` + retensi backup di luar repo). Keputusan adaptasi (termasuk apakah pesan warga pra-transaksi juga perlu dicakup) menunggu keputusan terbuka pada Bagian 2.

## 5. Hasil retrieval offline vs seed/query/rollback PostgreSQL

Dipisahkan secara eksplisit:

- **Retrieval offline (fixture JSONL, tanpa DB, tanpa tuning V7/V8)** — dijalankan di worktree integrasi dengan `search_chunks()` hasil port + stub DB yang melempar error bila tersentuh (menjamin tidak ada akses database). Catatan jujur: `backend/evaluate_runtime.py` tidak dapat dieksekusi langsung di lingkungan ini karena `services/rag_service.py` mengimpor `database.db` yang membutuhkan `psycopg` (tidak terinstal) — sehingga regresi dijalankan lewat skrip inline yang memuat ulang corpus persis seperti `load_chunks()` evaluator yang disepakati (fixture publik + 7 baris bylaw lokal):
  - Korpus: `backend/chatbot/dataset/knowledgebase.jsonl` (33 baris; 20 referensi publik pemerintah lolos filter `kelayakan_rag`, ID RTC-001..RTC-033) + 7 baris bylaw lokal ala `evaluate_runtime.BYLAWS` = **27 chunk**. Tidak ada penambahan template WhatsApp. Tidak ada perubahan threshold, bobot, label, atau dataset untuk mencapai hasil ini — ranking memakai konstanta hasil port (`AKSI_BOOST=0.15`, `ACTION_CONFLICT_PENALTY`, guard domisili/multi-topik, `MIN_LOCAL_COVERAGE=0.80`) apa adanya. Baseline pembanding: HEAD memakai `AKSI_BOOST=0.05` tanpa guard `cek_keamanan`/`semua_topik`/`ACTION_CONFLICT_PENALTY` (hasil HEAD tidak diklaim karena fungsi guard belum ada di HEAD).
  - Perintah aktual: `cd backend && python regresi_retrieval_offline.py --out ../docs/audit/bukti/retrieval_offline_2026-11-12.csv` (harness `backend/regresi_retrieval_offline.py`, dapat dijalankan ulang; memakai `search_chunks` + `CASES`/`load_chunks()` evaluator yang disepakati: `RELEVAN` 15 + `RELEVAN_RT` 5 + khusus 6, tanpa DB).
  - Hasil aktual: **RELEVAN Top-1 15/15, RT lokal 5/5, khusus (RAHASIA/LUAR_CAKUPAN/BELUM_ADA_SOP_RT) 6/6 — total 26/26 PASS**. Bukti terstruktur: `docs/audit/bukti/retrieval_offline_2026-11-12.csv` (26 baris + header `sep=,`, kolom pertanyaan/jenis/expected/top_source/status/similarity_score/base_score/correct/latency_ms).
- **Hasil verifikasi port RAG Supabase (tanpa eksekusi DB)** — diverifikasi dari kode + skema di worktree:
  - `services/rag_service.py:318-331` `search_knowledge_base()` memakai `query_all` Postgres (`SELECT ... FROM knowledgechunk c JOIN knowledgebase k ...`) lalu mendelegasikan ranking ke `search_chunks()` yang sama dengan harness offline — tidak ada sisa sintaks/driver MySQL (`pymysql`, backtick, `chat_messages` lama) di file hasil port.
  - `backend/database/migrate.py` menerapkan `supabase_sql/001..004` secara idempoten; kolom RAG (`knowledgechunk.kata_kunci`, `knowledgechunk.kode_sumber` + indeks) dibuat di `002_extensions.sql:53-55`; tabel chatbot (`chatsession/chatmessage/knowledgebase/knowledgechunk/retrievallog`) di-RLS-kan di baris 83-87.
  - `backend/database/seed.py` memuat `chatbot/dataset/knowledgebase.jsonl` (filter `pemerintah` + `REFERENSI_PUBLIK_DENGAN_LABEL_INSTANSI`), idempoten judul + menautkan `kode_sumber` pada dokumen lama; bylaw lokal di-seed per baris seperti harness.
  - Jalur tulis endpoint (`routes/chatbot_routes.py:36-92`) memakai nama tabel Supabase (`chatsession/chatmessage/retrievallog`) + `transaction()`; respons mengekspos `source_id/citation/similarity_score/base_score`, riwayat dibaca via JOIN `chatmessage LEFT JOIN retrievallog` — konsisten dengan skema port.
- **Seed PostgreSQL (eksekusi)**: **SKIP** — skema `supabase_sql/*.sql` dan `seed.py` Supabase tidak dieksekusi di sini karena tidak ada database uji terisolasi yang tersedia; tidak ada kredensial `SUPABASE_DB_URL` di lingkungan ini dan `psycopg` tidak terinstal pada interpreter aktif. Tidak diklaim sebagai PASS.
- **Query langsung PostgreSQL (`search_knowledge_base`)**: **SKIP** — alasan sama; query menunjuk tabel `knowledgechunk`/`knowledgebase` Supabase yang belum terisi di lingkungan ini. Tidak diklaim sebagai PASS.
### 5.1 Uji integrasi endpoint TanyaRT pada Postgres terisolasi — SKIP (database uji belum tersedia)

Rencana uji yang diminta (tidak dijalankan): (a) seed knowledge base; (b) satu pertanyaan bersumber jelas via `POST /api/v1/chatbot/query`; (c) cek `source_id`/citation pada respons; (d) cek pesan warga + balasan AI tersimpan di riwayat via `GET /api/v1/chatbot/sessions/<id>/messages`. Alasan SKIP: tidak ada kredensial database uji (`SUPABASE_DB_URL`/`DATABASE_URL`/`POSTGRES_URL` kosong, tidak ada file `.env`), tidak ada server Postgres lokal (`psql`/`pg_ctl`/`postgres` tidak ditemukan, `docker` tidak tersedia), dan driver `psycopg` tidak terinstal pada interpreter aktif — sehingga `migrate`, `seed`, `search_knowledge_base` (query langsung), maupun endpoint Flask tidak dapat dieksekusi tanpa menyentuh database produksi (dilarang). Status ini menggantikan klaim apa pun sebelumnya: tidak diklaim sebagai PASS.

Kriteria lolos bila database disposable tersedia: `python -m database.migrate` OK; `python -m database.seed` memuat 20 referensi publik + bylaw; `POST /api/v1/chatbot/query` ("Bagaimana mengurus KTP yang hilang di Surabaya?") mengembalikan `source_id` RTC-014/RTC-033 + `citation` tak kosong; riwayat memuat pesan warga tersanitasi + balasan AI + entri `retrievallog`; `roles_accepted('warga')` dipertahankan. Tidak ada test yang dijalankan pada database produksi.

- **Rollback transaksional**: **SKIP pada live DB** — logika `transaction()` dipertahankan apa adanya dari main; failure injection end-to-end (insert AI gagal mid-transaction) hanya dapat dibuktikan pada Postgres disposable. Tidak diklaim sebagai PASS.

Perintah yang dijalankan di worktree integrasi (semua lolos): `ast.parse` ketiga file hasil port (termasuk `routes/chatbot_routes.py`); verifikasi simbol (`semua_topik`, `cek_keamanan`, `mask_pii`, `is_sensitive_credential_for_storage`, `contains_raw_ssh_or_seed_phrase`, `ACTION_CONFLICT_PENALTY`, guard multi-topik/domisili); uji fungsi murni sanitasi/aturan (21/21 PASS: F1-set 15/15 + F2-set 6/6); regresi `cek_keamanan` (9/9) dan `mask_pii` (10/10); verifikasi tidak ada impor/driver MySQL (`pymysql`, `chat_messages` lama) pada file hasil port; verifikasi skema/migrasi/seed Supabase tidak tersentuh.

## 5.2 Temuan terbuka sanitasi (tidak diperbaiki pada putaran ini)

### 5.2.1 False negative: payload koma dengan titik sebelum kata terakhir

Varian payload sintetis 12 kata yang dipisah koma tetapi diakhiri titik sebelum kata terakhir (`seed phrase: abandon, ability, ..., abuse, access. account`) menghasilkan `contains_raw_ssh_or_seed_phrase() = False` dan `is_sensitive_credential_for_storage() = False` (harusnya True; terkonfirmasi di worktree ini). Diagnosis: token `access.` mengandung titik sehingga gagal pada filter kata `re.fullmatch(r'[a-zA-Z]{3,12}', ...)` — hanya 11 kata valid terhitung, di bawah ambang 12. Dicatat sebagai **temuan terbuka**; tidak ada pola sanitasi baru, tidak ada tuning ranking, blind V8 tetap tertutup.

### 5.2.2 False positive: prosa edukatif panjang tanpa payload

Prosa edukatif tanpa payload `Apa itu seed phrase dan bagaimana cara menjaganya? Panduan pemula membahas risiko pencurian aset digital melalui aplikasi palsu, perangkat rusak, kebocoran cadangan, serta praktik pemulihan akun.` menghasilkan `contains_raw_ssh_or_seed_phrase() = True` dan `is_sensitive_credential_for_storage() = True` (harusnya False; terkonfirmasi di worktree ini). Diagnosis: teks 24 kata alfabet digeser lewat jendela 12 kata; rentang offset 6 (`cara, panduan, pemula, membahas, risiko, pencurian, aset, digital, melalui, aplikasi, palsu, perangkat`) hanya memuat 1 kata fungsi (`cara`), di bawah ambang tolak `>= 2`, sehingga lolos sebagai "payload". Dicatat sebagai **temuan terbuka**; tidak ada pola sanitasi baru, tidak ada tuning ranking, blind V8 tetap tertutup.

## 6. Pekerjaan yang masih terbuka

1. Runner integrasi Supabase baru (pengganti mock MySQL) + suite regresi retrieval/privasi di atas database disposable terisolasi.
2. Verifikasi seed + SELECT langsung (`migrate`, `seed`, `search_knowledge_base`, reseed/duplikasi), uji endpoint satu-pertanyaan + cek riwayat (lihat 5.1), dan failure injection transaksional pada Postgres disposable.
5. Perbaikan temuan terbuka 5.2.1 (tokenizer sanitasi terhadap tanda titik) dan 5.2.2 (ambang jendela geser vs prosa edukatif panjang) — menunggu keputusan desain, bukan tuning retrieval.
3. Keputusan adaptasi `sanitize_historical_chat.py` ke skema Supabase (termasuk backup di luar repo, retensi, idempotensi, rollback) — tetap OPEN, tanpa eksekusi pada data nyata.
4. Keputusan SRS atas cakupan peran endpoint (`roles_accepted('warga')` dipertahankan; tidak dilonggarkan ke RT/admin tanpa dasar SRS) dan kebijakan multiwilayah.
