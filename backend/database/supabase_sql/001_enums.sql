-- 001_enums.sql
-- Menambah nilai enum yang dipakai kode RTConnect. Aman dijalankan berulang
-- (IF NOT EXISTS) dan tidak menghapus / mengubah nilai yang sudah ada.

ALTER TYPE public.pengirim_enum ADD VALUE IF NOT EXISTS 'warga';
ALTER TYPE public.pengirim_enum ADD VALUE IF NOT EXISTS 'sistem_ai';
ALTER TYPE public.pengirim_enum ADD VALUE IF NOT EXISTS 'rt';

ALTER TYPE public.status_chat_enum ADD VALUE IF NOT EXISTS 'berlangsung';
ALTER TYPE public.status_chat_enum ADD VALUE IF NOT EXISTS 'terjawab';
ALTER TYPE public.status_chat_enum ADD VALUE IF NOT EXISTS 'dieskalasi';
ALTER TYPE public.status_chat_enum ADD VALUE IF NOT EXISTS 'selesai';

ALTER TYPE public.penerima_tipe_enum ADD VALUE IF NOT EXISTS 'warga';
ALTER TYPE public.penerima_tipe_enum ADD VALUE IF NOT EXISTS 'rt';

ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'diajukan';
ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'perlu_revisi';
ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'disetujui';
ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'ditolak';
ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'siap_diambil';
ALTER TYPE public.status_pengajuan_enum ADD VALUE IF NOT EXISTS 'selesai';

ALTER TYPE public.jenis_ttd_enum ADD VALUE IF NOT EXISTS 'digital';
ALTER TYPE public.jenis_ttd_enum ADD VALUE IF NOT EXISTS 'basah';

ALTER TYPE public.status_konfirmasi_ttd_enum ADD VALUE IF NOT EXISTS 'pending';
ALTER TYPE public.status_konfirmasi_ttd_enum ADD VALUE IF NOT EXISTS 'dikonfirmasi';

ALTER TYPE public.status_pengambilan_enum ADD VALUE IF NOT EXISTS 'siap_diambil';
ALTER TYPE public.status_pengambilan_enum ADD VALUE IF NOT EXISTS 'sudah_diambil';