-- 004_alamat_surabaya.sql
-- Revisi wilayah RTConnect: RT 04 / RW 09 Perumahan Gunungsari Indah,
-- Kelurahan Kedurus, Kecamatan Karang Pilang, Kota Surabaya.
-- Memperbarui data yang sudah tersimpan. Aman dijalankan berulang.

-- Nilai bawaan RT/RW untuk akun baru
ALTER TABLE public.warga ALTER COLUMN nomor_rt SET DEFAULT '04';
ALTER TABLE public.warga ALTER COLUMN nomor_rw SET DEFAULT '09';
ALTER TABLE public.rt    ALTER COLUMN nomor_rt SET DEFAULT '04';
ALTER TABLE public.rt    ALTER COLUMN nomor_rw SET DEFAULT '09';

-- Akun lama yang masih memakai RT 032 / RW 08
UPDATE public.warga SET nomor_rt = '04', nomor_rw = '09' WHERE nomor_rt = '032' AND nomor_rw = '08';
UPDATE public.rt    SET nomor_rt = '04', nomor_rw = '09' WHERE nomor_rt = '032' AND nomor_rw = '08';

-- Basis pengetahuan chatbot yang menyebut wilayah lama
UPDATE public.knowledgebase
   SET judul = replace(judul, 'RT 032 / RW 08 Griya Taman Asri', 'RT 04 / RW 09 Gunungsari Indah'),
       isi_dokumen = replace(
           replace(isi_dokumen, 'RT 032 / RW 08 Griya Taman Asri', 'RT 04 / RW 09 Gunungsari Indah'),
           'di rumah Ketua RT pada jam', 'di rumah Ketua RT (Gunungsari Indah Blok YY No. 22) pada jam')
 WHERE judul LIKE '%Griya Taman Asri%' OR isi_dokumen LIKE '%Griya Taman Asri%'
    OR isi_dokumen LIKE '%di rumah Ketua RT pada jam%';

UPDATE public.knowledgechunk
   SET isi_chunk = replace(
           replace(isi_chunk, 'RT 032 / RW 08 Griya Taman Asri', 'RT 04 / RW 09 Gunungsari Indah'),
           'di rumah Ketua RT pada jam', 'di rumah Ketua RT (Gunungsari Indah Blok YY No. 22) pada jam'),
       kata_kunci = replace(kata_kunci, 'RT 032 / RW 08 Griya Taman Asri', 'RT 04 / RW 09 Gunungsari Indah')
 WHERE isi_chunk LIKE '%Griya Taman Asri%' OR isi_chunk LIKE '%di rumah Ketua RT pada jam%'
    OR kata_kunci LIKE '%Griya Taman Asri%';
