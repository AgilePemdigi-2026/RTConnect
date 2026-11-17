# Deploy RTConnect ke Coolify (Server CAIIS "aorus")

Dokumen ini menyiapkan RTConnect agar dapat di-deploy oleh dosen/admin di Coolify server CAIIS
(lihat `indrakharisma/ai-server` → `docs/server-aorus.md`). Mahasiswa **tidak** memiliki login
Coolify; deploy dilakukan oleh dosen setelah permintaan lewat email.

## 1. Arsitektur yang di-deploy

Satu container (Dockerfile di **root repo**) berisi:

| Path | Isi |
|---|---|
| `https://<nama-app>.caiis.ai.id/` | Aplikasi Flutter Web (hasil `flutter build web`) |
| `https://<nama-app>.caiis.ai.id/api/v1/...` | REST API Flask (Gunicorn) |
| `https://<nama-app>.caiis.ai.id/api/v1/health` | Health check (cek koneksi database) |

Karena web dan API berada di domain yang sama, Flutter Web otomatis memakai `<domain>/api/v1`
tanpa perlu `--dart-define`.

Layanan eksternal yang dipakai container (butuh akses internet keluar):
- **Supabase** – PostgreSQL (data) dan Storage S3 (PDF, tanda tangan, lampiran).
- **Gemini API** – opsional, bila tidak memakai LLM server kampus.

## 2. Pengaturan Coolify (untuk dosen/admin)

| Pengaturan | Nilai |
|---|---|
| Repository | `https://github.com/AgilePemdigi-2026/RTConnect` (publik) |
| Branch | `main` |
| Build pack | **Dockerfile** (`/Dockerfile` di root repo) |
| Port aplikasi | `5000` |
| Domain | `https://rtconnect.caiis.ai.id` (atau subdomain lain yang disetujui) |
| Health check | `GET /api/v1/health` |
| Volume persisten | Tidak perlu (file disimpan di Supabase Storage) |

## 3. Environment variables

Nilai rahasia **dikirim terpisah** ke dosen (bukan lewat repo / email biasa).

| Variabel | Wajib | Keterangan |
|---|---|---|
| `APP_ENV` | ya | `production` (sudah default di Dockerfile) |
| `PORT` | – | Default `5000` |
| `JWT_SECRET` | ya | Acak, minimal 32 karakter: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `SUPABASE_DB_URL` | ya | `postgresql://postgres.<ref>:<password>@<pooler-host>:5432/postgres` |
| `STORAGE_BACKEND` | ya | `s3` |
| `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL` | ya | Bucket Supabase Storage, `ap-northeast-2`, endpoint `https://<ref>.storage.supabase.co/storage/v1/s3` |
| `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | ya | Kunci S3 Supabase |
| `CORS_ORIGINS` | ya | Persis domain aplikasi, mis. `https://rtconnect.caiis.ai.id` |
| `RT_SIGNING_PIN_HASH` | ya | Hash bcrypt PIN Ketua RT: `python -m database.hash_rt_pin` |
| `RT_WHATSAPP_NUMBER` | ya | Format internasional angka saja, mis. `6281234567890` |
| `RT_NUMBER`, `RW_NUMBER`, `RT_LETTER_CODE` | ya | `04`, `09`, `GSI` |
| `RT_AREA`, `RT_SIGNING_LOCATION`, `RT_KELURAHAN`, … | ya | Identitas RT 04 RW 09 Gunungsari Indah (lihat `backend/.env.example`) |
| `LLM_BASE_URL` | opsional | `http://192.168.88.217:11434/v1` → asisten AI surat memakai LLM server kampus |
| `LLM_API_KEY` | opsional | `ollama` |
| `LLM_MODEL` | opsional | `gemma4:12b` (rekomendasi server, bahasa Indonesia baik) |
| `GEMINI_API_KEY` | opsional | Dipakai asisten AI surat bila `LLM_BASE_URL` kosong; juga dipakai TanyaRT |
| `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `TANYART_LLM_TIMEOUT` | sesuai tim | Konfigurasi TanyaRT, salin dari `.env` tim |
| `GUNICORN_TIMEOUT` | – | Default `180` detik (LLM server bisa butuh 10–30 dtk saat model dimuat) |
| `WEB_CONCURRENCY` | – | Default `2` worker |
| `RUN_MIGRATIONS` | – | `true` hanya bila database perlu dimigrasi saat start |

Production sengaja **gagal start** bila `JWT_SECRET`, `RT_SIGNING_PIN_HASH` (bcrypt),
`SUPABASE_DB_URL`, S3, `CORS_ORIGINS` (https, tanpa `*`), atau `RT_WHATSAPP_NUMBER` tidak valid.
Bila container langsung berhenti, cek log Coolify untuk pesan `Production requires ...`.

## 4. Asisten AI surat dengan LLM server kampus

- Bila `LLM_BASE_URL` diisi, asisten AI pengisi formulir memakai API OpenAI-compatible (Ollama)
  di server; bila kosong, memakai Gemini.
- LLM server hanya bisa diakses dari aplikasi yang berjalan di Coolify (LAN). Untuk uji di laptop,
  pakai Gemini atau Ollama lokal (`LLM_BASE_URL=http://localhost:11434/v1`).
- NIK, nomor KK, agama, dan nomor HP tetap **tidak** dikirim ke model.
- Jika model sedang dimuat/antre dan gagal, formulir tetap terisi dari biodata tersimpan.
- TanyaRT tidak diubah dan tetap memakai konfigurasinya sendiri.

## 5. Uji lokal sebelum mengirim permintaan

```sh
# dari root repo (butuh Docker Desktop); backend/.env = .env yang biasa dipakai tim
docker build -t rtconnect .
docker run --rm -p 5000:5000 --env-file backend/.env -e APP_ENV=development rtconnect
```

Buka `http://localhost:5000` (aplikasi) dan `http://localhost:5000/api/v1/health` (status API).
`APP_ENV=development` dipakai karena validasi production mewajibkan `CORS_ORIGINS` berupa https.

## 6. Akun

Database Supabase yang sudah berjalan tetap dipakai, sehingga akun Ketua RT dan warga yang sudah
ada tetap berlaku. Akun demo diblokir di production. Bila memakai database baru, buat akun Ketua RT
lewat shell satu kali: `python -m database.create_rt_user`.

## 7. Template email permintaan deploy

```
Kepada: indra.kharisma@fst.unair.ac.id
Subjek: [Coolify caiis] RTConnect - <NAMA> - <NIM>

Yth. Bapak Indra Kharisma,

Saya <NAMA> (<NIM>), Kelompok 3 kelas I1 Pembangunan Perangkat Lunak, memohon deploy aplikasi
RTConnect di Coolify server CAIIS.

1. Nama & fungsi aplikasi : RTConnect – layanan administrasi RT 04 RW 09 Gunungsari Indah
   (pengajuan & pengesahan surat pengantar, asisten AI pengisi formulir, chatbot TanyaRT).
2. Repository             : https://github.com/AgilePemdigi-2026/RTConnect (publik)
3. Branch                 : main
4. Tech stack             : Flutter Web + Python Flask (Gunicorn), satu Dockerfile di root repo
5. Port                   : 5000 (membaca env PORT, listen 0.0.0.0)
6. Health check           : /api/v1/health
7. Environment variables  : APP_ENV, JWT_SECRET, SUPABASE_DB_URL, STORAGE_BACKEND,
                            S3_BUCKET, S3_REGION, S3_ENDPOINT_URL, S3_ACCESS_KEY_ID,
                            S3_SECRET_ACCESS_KEY, CORS_ORIGINS, RT_SIGNING_PIN_HASH,
                            RT_WHATSAPP_NUMBER, RT_* (identitas RT), LLM_BASE_URL, LLM_API_KEY,
                            LLM_MODEL, GEMINI_API_KEY, EMBEDDING_* (TanyaRT)
                            (nilai akan saya kirim terpisah secara aman)
8. Database / storage     : Supabase (PostgreSQL + Storage) eksternal; tidak perlu volume
9. Subdomain              : rtconnect.caiis.ai.id
10. LLM                   : Ya, gemma4:12b untuk asisten AI pengisi formulir surat
11. Kaitan                : Proyek mata kuliah Pembangunan Perangkat Lunak (Sprint 1–2)

Terima kasih.
<NAMA>
```
