-- Catatan ketepatan asisten AI pengisi formulir (untuk evaluasi).
-- Satu baris per pengajuan yang dibuat lewat asisten AI.
CREATE TABLE IF NOT EXISTS public.ai_fill_log (
    log_id         serial PRIMARY KEY,
    pengajuan_id   integer NOT NULL REFERENCES public.pengajuansurat (pengajuan_id) ON DELETE CASCADE,
    warga_id       integer NOT NULL,
    model          varchar(80),
    jumlah_pesan   smallint NOT NULL DEFAULT 1,
    kolom_ai       jsonb NOT NULL DEFAULT '[]'::jsonb,   -- kolom yang diisi AI
    kolom_diubah   jsonb NOT NULL DEFAULT '[]'::jsonb,   -- kolom isian AI yang diubah warga
    jumlah_ai      smallint NOT NULL DEFAULT 0,
    jumlah_diubah  smallint NOT NULL DEFAULT 0,
    dibuat_pada    timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ai_fill_log_pengajuan ON public.ai_fill_log (pengajuan_id);
