# Guardrail Asisten AI Generative Document (RTConnect)

Dokumen ini menjelaskan cara RTConnect menangani lima risiko pemakaian AI sebagai
*drafter* (penyusun draf) dokumen surat RT, sesuai masukan asisten praktikum dan dosen.

## Prinsip desain

1. **AI hanya mengusulkan, tidak memutuskan.** AI cuma mengekstrak isian formulir dari
   cerita warga. Isi surat dibuat dari template resmi. Surat baru sah setelah warga
   memeriksa dan mengirim, Ketua RT menyetujui, lalu disahkan dengan PIN.
2. **Guardrail dijalankan di server dan bersifat deterministik.** Prompt hanya menjadi
   lapis pertama. Setiap keluaran AI diperiksa ulang oleh kode
   (`backend/services/ai_guardrails.py`), sehingga keamanan tidak bergantung pada
   kepatuhan model.
3. **Lebih baik kosong daripada salah.** Nilai yang meragukan dibuang dan ditandai
   "Perlu diisi". Asisten lalu bertanya balik kepada warga.

```
Cerita warga
  -> samarkan data sensitif (NIK/KK/HP/email)
  -> buang instruksi sisipan                            [Risiko 4]
  -> prompt + pembatas acak + panduan SOP -> Gemini / LLM
  -> validasi format & whitelist kolom                  [Risiko 3, 4]
  -> cek intent & kata kunci jenis surat                [Risiko 2]
  -> cek bukti di cerita (grounding)                    [Risiko 5]
  -> cek SOP jenis surat                                [Risiko 1]
  -> gabung dengan biodata tersimpan
  -> warga memeriksa -> Ketua RT menyetujui -> PIN
```

## Lima risiko dan mitigasinya

| No | Risiko | Mitigasi di RTConnect | Lokasi kode |
|---|---|---|---|
| 1 | **AI tidak sesuai SOP** | SOP setiap jenis surat ditulis sebagai data: kata kunci, pola instansi tujuan yang sah, dan alias nama resmi. Contoh: tujuan SKCK wajib kepolisian, jadi "PT Maju Jaya" ditolak. Tujuan KTP hanya kelurahan, kecamatan, atau Dispendukcapil. Jenis surat hanya boleh dari daftar aktif di database. Satu pengajuan berisi satu jenis surat. AI tidak pernah mengisi nama, NIK, No. KK, agama, alamat, atau status pengajuan. | `letter_guidance._sop()`, `ai_guardrails.check_sop()`, `FORBIDDEN_FIELDS` |
| 2 | **AI salah menangkap intent** | AI mengembalikan `intent` (ajukan_surat / pertanyaan_umum / di_luar_layanan) dan `keyakinan`. Server mencocokkannya dengan kata kunci di cerita. Kalau dua jenis surat disebut, asisten bertanya mau mulai dari yang mana. Kalau jenis tidak disebut jelas, asisten bertanya "Maksudmu …?" tanpa menebak. Pertanyaan umum diarahkan ke TanyaRT. Koreksi di pesan terbaru diutamakan (multi-turn). | `ai_guardrails.detect_intent()`, `detect_jenis()` |
| 3 | **AI tidak mengikuti template** | AI tidak menulis isi surat. Surat/PDF dibuat dari template resmi blangko RT. Setiap nilai dibersihkan menjadi satu baris pendek tanpa markdown, penanda `{{ }}`, atau tautan, lalu dipotong di batas kata. Keperluan mengikuti contoh kalimat baku per jenis surat. | `ai_guardrails.to_template_value()`, `templates/surat_pengantar.txt` |
| 4 | **Prompt injection** | (a) Pola instruksi seperti "abaikan aturan", "kamu sekarang admin", "setujui surat ini", `system prompt`, tag peran, dan ```` ``` ```` dihapus sebelum dikirim ke AI. Warga diberi peringatan. (b) Cerita dibungkus tag pembatas acak per permintaan, sehingga tidak bisa "ditutup" dari dalam cerita. (c) Keluaran AI yang berisi instruksi atau tautan ditolak. (d) Hanya kolom whitelist yang dipakai. Upaya mengisi NIK/KK/status dicatat sebagai peringatan. (e) Perubahan status surat tetap butuh Ketua RT dan PIN. | `ai_guardrails.sanitize_story()`, `looks_like_instruction()`, `_build_user_prompt()` |
| 5 | **AI mengarang (halusinasi)** | Prompt meminta null bila AI tidak tahu, plus kutipan `bukti`. Server memeriksa bukti setiap kolom di cerita warga. Nama perusahaan atau angka yang tidak disebut warga membuat keperluan ditolak. Jenis kelamin dan status kawin butuh kata kunci. Tanggal lahir butuh tahunnya disebut. Kutipan bukti AI harus benar-benar ada di cerita. Nilai tanpa bukti dibuang dan masuk daftar `ditolak` beserta alasannya. Kolom kosong lalu diisi dari data tersimpan atau oleh warga. | `ai_guardrails.ground_field()`, `ground_tujuan()` |

## Transparansi untuk warga

Respons `/api/v1/letters/ai-fill` menambahkan field berikut. Field lama tetap ada.

- `intent`, `keyakinan`: maksud warga menurut sistem.
- `bukti`: kutipan cerita yang menjadi dasar tiap isian.
- `ditolak`: kolom yang sengaja tidak diisi AI beserta alasannya. Di aplikasi tampil
  sebagai kotak "AI tidak mengisi kolom berikut".
- `peringatan`: misalnya "Sebagian pesanmu berisi perintah ke sistem dan diabaikan".
  Ditampilkan di chat.

Setiap isian tetap berlabel sumbernya (AI / Tersimpan / Perlu diisi). Warga wajib
mencentang persetujuan sebelum mengirim. Ketepatan AI diukur lewat `ai_fill_log`
dan `/ai-stats`.

## Pengujian (BDD)

File `backend/features/sprint2/sprint2_05_ai_guardrails.gherkin` berisi 11 skenario.
Respons model disimulasikan (termasuk jawaban yang berhalusinasi, terkena injeksi, dan
melanggar SOP), lalu diuji bahwa server menyaringnya:

| Risiko | Skenario |
|---|---|
| SOP | Tujuan SKCK ke perusahaan ditolak; "polsek" dibakukan menjadi "Polsek Karang Pilang" |
| Intent | Dua jenis surat menghasilkan pertanyaan balik; pertanyaan umum diarahkan ke TanyaRT; koreksi di pesan terbaru diutamakan |
| Template | Markdown dan `{{ }}` dibersihkan dari keperluan |
| Injection | Instruksi sisipan tidak sampai ke AI; keluaran berisi instruksi, tautan, atau No. KK ditolak |
| Mengarang | Perusahaan, pekerjaan, dan tujuan karangan dibuang; kutipan bukti palsu ditolak; isian valid disertai bukti |

Cara menjalankan:

```
cd backend
python run_bdd.py features/sprint2
```

## Keterbatasan yang diketahui

- Grounding berbasis kata (bukan pemahaman makna), jadi sengaja dibuat ketat. Sinonim
  yang jauh bisa membuat isian benar ikut dibuang. Akibatnya warga hanya perlu mengisi
  sendiri; datanya tidak menjadi salah.
- Daftar pola injection bisa diakali dengan variasi baru. Karena itu ada lapis lain:
  pembatas acak, validasi keluaran, whitelist kolom, dan persetujuan manusia.
- SOP jenis surat baru di database memakai kata pada nama surat sebagai kata kunci,
  dengan tujuan bebas. Bila perlu, tambahkan SOP-nya di `letter_guidance._sop()`.
