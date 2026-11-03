-- 003_data_pemohon.sql
-- Data lengkap pemohon disimpan PER PENGAJUAN (salinan kondisi saat surat diajukan),
-- mengikuti format Surat Pengantar / Keterangan RT. Hanya MENAMBAH kolom; aman diulang.

ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS pekerjaan varchar(100);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS jenis_kelamin varchar(20);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS tempat_lahir varchar(100);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS tanggal_lahir date;
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS agama varchar(40);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS status_kawin varchar(20);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS kewarganegaraan varchar(50) DEFAULT 'WNI';
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS nomor_kk varchar(16);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS instansi_tujuan varchar(150);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS keterangan_lain varchar(255);
