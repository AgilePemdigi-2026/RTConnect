-- 002_extensions.sql
-- Menambah kolom & tabel yang dibutuhkan fitur RTConnect (nomor surat resmi,
-- QR verifikasi, kunci PIN RT, lampiran, judul/tipe notifikasi, dll).
-- Hanya MENAMBAH; tidak ada kolom/tabel Anda yang dihapus. Aman dijalankan berulang.

-- ---------- warga & rt ----------
ALTER TABLE public.warga ADD COLUMN IF NOT EXISTS nomor_rt varchar(5) DEFAULT '032';
ALTER TABLE public.warga ADD COLUMN IF NOT EXISTS nomor_rw varchar(5) DEFAULT '08';
ALTER TABLE public.warga ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
ALTER TABLE public.rt    ADD COLUMN IF NOT EXISTS nomor_rt varchar(5) DEFAULT '032';
ALTER TABLE public.rt    ADD COLUMN IF NOT EXISTS nomor_rw varchar(5) DEFAULT '08';
ALTER TABLE public.rt    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

CREATE UNIQUE INDEX IF NOT EXISTS ux_warga_nik   ON public.warga (nik);
CREATE UNIQUE INDEX IF NOT EXISTS ux_warga_email ON public.warga (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS ux_rt_nik      ON public.rt (nik);
CREATE UNIQUE INDEX IF NOT EXISTS ux_rt_email    ON public.rt (lower(email));

-- ---------- jenissurat ----------
ALTER TABLE public.jenissurat ADD COLUMN IF NOT EXISTS kode_surat varchar(20);
ALTER TABLE public.jenissurat ADD COLUMN IF NOT EXISTS persyaratan_dokumen text;
ALTER TABLE public.jenissurat ADD COLUMN IF NOT EXISTS is_aktif boolean NOT NULL DEFAULT true;
CREATE UNIQUE INDEX IF NOT EXISTS ux_jenissurat_kode ON public.jenissurat (kode_surat);

-- ---------- pengajuansurat ----------
ALTER TABLE public.pengajuansurat ALTER COLUMN tujuan_surat TYPE text;
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS nomor_pengajuan varchar(50);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS metode_tanda_tangan varchar(10) NOT NULL DEFAULT 'digital';
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS berkas_lampiran_url varchar(512);
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS tanggal_diverifikasi timestamp;
ALTER TABLE public.pengajuansurat ADD COLUMN IF NOT EXISTS tanggal_selesai timestamp;
CREATE UNIQUE INDEX IF NOT EXISTS ux_pengajuan_nomor ON public.pengajuansurat (nomor_pengajuan);
CREATE INDEX IF NOT EXISTS ix_pengajuan_warga ON public.pengajuansurat (warga_id);
CREATE INDEX IF NOT EXISTS ix_draft_pengajuan ON public.draftsurat (pengajuan_id);

-- ---------- suratfinal ----------
ALTER TABLE public.suratfinal ADD COLUMN IF NOT EXISTS nomor_surat_resmi varchar(100);
ALTER TABLE public.suratfinal ADD COLUMN IF NOT EXISTS qr_verification_token varchar(128);
ALTER TABLE public.suratfinal ADD COLUMN IF NOT EXISTS signature_image_path varchar(255);
CREATE UNIQUE INDEX IF NOT EXISTS ux_suratfinal_pengajuan ON public.suratfinal (pengajuan_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_suratfinal_nomor ON public.suratfinal (nomor_surat_resmi);
CREATE UNIQUE INDEX IF NOT EXISTS ux_suratfinal_qr ON public.suratfinal (qr_verification_token);

-- ---------- notifikasi ----------
ALTER TABLE public.notifikasi ALTER COLUMN isi_notifikasi TYPE text;
ALTER TABLE public.notifikasi ADD COLUMN IF NOT EXISTS tipe_notifikasi varchar(40);
ALTER TABLE public.notifikasi ADD COLUMN IF NOT EXISTS judul varchar(100);
ALTER TABLE public.notifikasi ADD COLUMN IF NOT EXISTS tautan_tujuan varchar(255);
CREATE INDEX IF NOT EXISTS ix_notifikasi_warga ON public.notifikasi (warga_id);
CREATE INDEX IF NOT EXISTS ix_notifikasi_rt ON public.notifikasi (rt_id);

-- ---------- chatbot ----------
ALTER TABLE public.knowledgechunk ADD COLUMN IF NOT EXISTS kata_kunci varchar(255);
ALTER TABLE public.knowledgechunk ADD COLUMN IF NOT EXISTS kode_sumber varchar(20);
CREATE INDEX IF NOT EXISTS ix_chunk_kode_sumber ON public.knowledgechunk (kode_sumber);
CREATE INDEX IF NOT EXISTS ix_chatmessage_session ON public.chatmessage (chat_session_id);
CREATE INDEX IF NOT EXISTS ix_retrieval_message ON public.retrievallog (message_id);

-- ---------- tabel baru ----------
CREATE TABLE IF NOT EXISTS public.nomor_surat_counter (
  tahun smallint PRIMARY KEY,
  last_number integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.rt_pin_attempts (
  rt_id integer PRIMARY KEY REFERENCES public.rt (rt_id) ON DELETE CASCADE,
  gagal_count smallint NOT NULL DEFAULT 0,
  locked_until timestamp,
  updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

-- ---------- KEAMANAN: Row Level Security ----------
-- Tanpa policy, kunci publishable/anon TIDAK bisa membaca atau menulis tabel apa pun
-- (termasuk password_hash). Backend memakai koneksi database langsung (role postgres,
-- melewati RLS), jadi aplikasi tetap berjalan normal.
ALTER TABLE public.warga               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rt                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jenissurat          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pengajuansurat      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.draftsurat          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suratfinal          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifikasi          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatsession         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatmessage         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledgebase       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledgechunk      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.retrievallog        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nomor_surat_counter ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rt_pin_attempts     ENABLE ROW LEVEL SECURITY;