-- Migration: Tambah kolom fcm_token untuk push notifications di tabel warga dan rt
ALTER TABLE public.warga 
ADD COLUMN IF NOT EXISTS fcm_token VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS fcm_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.rt 
ADD COLUMN IF NOT EXISTS fcm_token VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS fcm_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_warga_fcm_token ON public.warga (fcm_token);
CREATE INDEX IF NOT EXISTS idx_rt_fcm_token ON public.rt (fcm_token);
