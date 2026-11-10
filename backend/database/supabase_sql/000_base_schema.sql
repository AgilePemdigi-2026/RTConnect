-- 000_base_schema.sql
-- Skema dasar PostgreSQL untuk lingkungan CI (GitHub Actions) atau database PostgreSQL baru.
-- Mendefinisikan tipe ENUM dan 12 tabel inti sebelum migrasi 001..004 dijalankan.
-- Aman dijalankan berulang (idempotent).

DO $$
BEGIN
    CREATE TYPE public.pengirim_enum AS ENUM ('warga', 'sistem_ai', 'pengurus', 'rt');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.status_chat_enum AS ENUM ('berlangsung', 'terjawab_chatbot', 'eskalasi', 'selesai', 'terjawab', 'dieskalasi');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.penerima_tipe_enum AS ENUM ('warga', 'pengurus', 'rt');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.status_pengajuan_enum AS ENUM ('menunggu_review', 'revisi', 'ditolak', 'disetujui', 'selesai', 'diajukan', 'perlu_revisi', 'siap_diambil');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.jenis_ttd_enum AS ENUM ('digital', 'basah');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.status_konfirmasi_ttd_enum AS ENUM ('pending', 'terkonfirmasi', 'gagal', 'dikonfirmasi');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.status_pengambilan_enum AS ENUM ('siap_diambil', 'sudah_diambil');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.warga (
    warga_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nik varchar(16) NOT NULL UNIQUE,
    nama varchar(100) NOT NULL,
    alamat varchar(255) NOT NULL,
    no_telp varchar(20),
    email varchar(100),
    password_hash varchar(255) NOT NULL,
    salt varchar(64),
    tanda_tangan_digital varchar(255),
    foto_profil varchar(512),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.rt (
    rt_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nik varchar(16) NOT NULL UNIQUE,
    nama varchar(100) NOT NULL,
    jabatan varchar(50) NOT NULL,
    no_telp varchar(20),
    email varchar(100),
    password_hash varchar(255) NOT NULL,
    salt varchar(64),
    tanda_tangan_digital varchar(255),
    foto_profil varchar(512),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.jenissurat (
    jenis_surat_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nama_jenis varchar(100) NOT NULL,
    template_surat text,
    butuh_ttd_basah boolean DEFAULT false
);

CREATE TABLE IF NOT EXISTS public.pengajuansurat (
    pengajuan_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warga_id integer NOT NULL REFERENCES public.warga (warga_id) ON DELETE CASCADE,
    jenis_surat_id integer NOT NULL REFERENCES public.jenissurat (jenis_surat_id),
    tujuan_surat text NOT NULL,
    tanggal_pengajuan timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status public.status_pengajuan_enum DEFAULT 'menunggu_review',
    alasan_penolakan varchar(255),
    catatan_revisi varchar(255),
    rt_id integer REFERENCES public.rt (rt_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.draftsurat (
    draft_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pengajuan_id integer NOT NULL REFERENCES public.pengajuansurat (pengajuan_id) ON DELETE CASCADE,
    isi_draft text NOT NULL,
    versi_ke integer DEFAULT 1,
    dibuat_oleh_ai boolean DEFAULT true,
    tanggal_dibuat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.suratfinal (
    surat_final_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pengajuan_id integer NOT NULL REFERENCES public.pengajuansurat (pengajuan_id) ON DELETE CASCADE,
    rt_id integer NOT NULL REFERENCES public.rt (rt_id),
    file_pdf_path varchar(255),
    jenis_ttd public.jenis_ttd_enum NOT NULL,
    status_konfirmasi_ttd public.status_konfirmasi_ttd_enum DEFAULT 'pending',
    tanggal_ttd timestamp without time zone,
    status_pengambilan public.status_pengambilan_enum DEFAULT 'siap_diambil',
    tanggal_terbit timestamp without time zone,
    tanggal_diambil timestamp without time zone
);

CREATE TABLE IF NOT EXISTS public.knowledgebase (
    knowledge_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    judul varchar(150) NOT NULL,
    kategori varchar(50),
    isi_dokumen text NOT NULL,
    sumber varchar(150),
    uploaded_by integer REFERENCES public.rt (rt_id) ON DELETE SET NULL,
    tanggal_upload timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.knowledgechunk (
    chunk_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    knowledge_id integer NOT NULL REFERENCES public.knowledgebase (knowledge_id) ON DELETE CASCADE,
    urutan_chunk integer NOT NULL,
    isi_chunk text NOT NULL,
    embedding_vector jsonb,
    tanggal_dibuat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.chatsession (
    chat_session_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warga_id integer NOT NULL REFERENCES public.warga (warga_id) ON DELETE CASCADE,
    status public.status_chat_enum DEFAULT 'berlangsung',
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS public.chatmessage (
    message_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chat_session_id integer NOT NULL REFERENCES public.chatsession (chat_session_id) ON DELETE CASCADE,
    pengirim public.pengirim_enum NOT NULL,
    isi_pesan text NOT NULL,
    intent_terdeteksi varchar(100),
    entity_terdeteksi varchar(100),
    tanggal_kirim timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.retrievallog (
    retrieval_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id integer NOT NULL REFERENCES public.chatmessage (message_id) ON DELETE CASCADE,
    chunk_id integer NOT NULL REFERENCES public.knowledgechunk (chunk_id) ON DELETE CASCADE,
    skor_relevansi numeric,
    tanggal_retrieval timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.notifikasi (
    notifikasi_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    penerima_tipe public.penerima_tipe_enum NOT NULL,
    warga_id integer REFERENCES public.warga (warga_id) ON DELETE CASCADE,
    rt_id integer REFERENCES public.rt (rt_id) ON DELETE CASCADE,
    pengajuan_id integer REFERENCES public.pengajuansurat (pengajuan_id) ON DELETE CASCADE,
    chat_session_id integer REFERENCES public.chatsession (chat_session_id) ON DELETE CASCADE,
    isi_notifikasi text NOT NULL,
    status_baca boolean DEFAULT false,
    tanggal_kirim timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
