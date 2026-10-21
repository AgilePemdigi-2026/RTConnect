-- ====================================================================
-- SKEMA BASIS DATA RESMI RTCONNECT (MySQL 8.0+ / 8.4 LTS)
-- Sesuai database.md & revisi UC-09 (TTD Digital Tempelan Gambar)
-- ====================================================================

-- 1. TABEL PENGGUNA TERPUSAT (UNIFIED USERS)
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INT AUTO_INCREMENT PRIMARY KEY,
  `nik` VARCHAR(16) NOT NULL UNIQUE,
  `nama_lengkap` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `nomor_telepon` VARCHAR(20) NOT NULL,
  `alamat` VARCHAR(255) NOT NULL,
  `nomor_rt` VARCHAR(5) DEFAULT '032',
  `nomor_rw` VARCHAR(5) DEFAULT '08',
  `role` ENUM('warga', 'rt', 'admin') NOT NULL DEFAULT 'warga',
  `tanda_tangan_url` VARCHAR(512) NULL COMMENT 'Object key untuk gambar tanda tangan',
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_users_nik` (`nik`),
  INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB;

-- 2. TABEL MASTER JENIS SURAT
CREATE TABLE IF NOT EXISTS `jenis_surat` (
  `jenis_surat_id` INT AUTO_INCREMENT PRIMARY KEY,
  `kode_surat` VARCHAR(20) NOT NULL UNIQUE,
  `nama_surat` VARCHAR(100) NOT NULL,
  `template_dokumen` TEXT NOT NULL COMMENT 'Template baku surat pengantar',
  `persyaratan_dokumen` TEXT NULL,
  `is_aktif` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. TABEL PENGAJUAN SURAT
CREATE TABLE IF NOT EXISTS `pengajuan_surat` (
  `pengajuan_id` INT AUTO_INCREMENT PRIMARY KEY,
  `nomor_pengajuan` VARCHAR(50) NOT NULL UNIQUE,
  `warga_id` INT NOT NULL,
  `rt_id` INT NULL,
  `jenis_surat_id` INT NOT NULL,
  `keperluan` TEXT NOT NULL,
  `metode_tanda_tangan` ENUM('digital', 'basah') NOT NULL DEFAULT 'digital',
  `berkas_lampiran_url` VARCHAR(512) NULL COMMENT 'Object key berkas lampiran',
  `draf_ai_konten` TEXT NULL COMMENT 'Draf surat hasil template deterministik',
  `status` ENUM('diajukan', 'perlu_revisi', 'disetujui', 'ditolak', 'siap_diambil', 'selesai') NOT NULL DEFAULT 'diajukan',
  `catatan_revisi` VARCHAR(255) NULL,
  `alasan_penolakan` VARCHAR(255) NULL,
  `tanggal_pengajuan` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `tanggal_diverifikasi` DATETIME NULL,
  `tanggal_selesai` DATETIME NULL,
  CONSTRAINT `fk_pengajuan_warga` FOREIGN KEY (`warga_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pengajuan_rt` FOREIGN KEY (`rt_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pengajuan_jenis` FOREIGN KEY (`jenis_surat_id`) REFERENCES `jenis_surat` (`jenis_surat_id`)
) ENGINE=InnoDB;

-- 4. TABEL SURAT FINAL (BERKAS PDF & PENGESAHAN)
CREATE TABLE IF NOT EXISTS `surat_final` (
  `surat_final_id` INT AUTO_INCREMENT PRIMARY KEY,
  `pengajuan_id` INT NOT NULL UNIQUE,
  `nomor_surat_resmi` VARCHAR(100) NOT NULL UNIQUE,
  `file_pdf_path` VARCHAR(512) NOT NULL COMMENT 'Object key PDF surat',
  `qr_verification_token` VARCHAR(128) NULL UNIQUE,
  `signature_image_path` VARCHAR(255) NULL COMMENT 'Path stempel tanda tangan digital yang disematkan',
  `status_pengesahan` ENUM('digital_sah', 'basah_selesai') NOT NULL,
  `tanggal_terbit` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `tanggal_diambil` DATETIME NULL,
  CONSTRAINT `fk_surat_pengajuan` FOREIGN KEY (`pengajuan_id`) REFERENCES `pengajuan_surat` (`pengajuan_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. BASIS PENGETAHUAN UNTUK PENCARIAN LEKSIKAL CHATBOT TANYA RT
CREATE TABLE IF NOT EXISTS `knowledge_base` (
  `knowledge_id` INT AUTO_INCREMENT PRIMARY KEY,
  `judul_dokumen` VARCHAR(150) NOT NULL,
  `kategori` VARCHAR(50) NOT NULL,
  `isi_dokumen` LONGTEXT NOT NULL,
  `diunggah_oleh_rt` INT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_kb_uploader` FOREIGN KEY (`diunggah_oleh_rt`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `knowledge_chunks` (
  `chunk_id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `urutan_chunk` INT NOT NULL,
  `isi_chunk` TEXT NOT NULL,
  `kata_kunci` VARCHAR(255) NULL,
  `embedding_vector` JSON NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_chunk_knowledge` FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge_base` (`knowledge_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `chat_sessions` (
  `session_id` INT AUTO_INCREMENT PRIMARY KEY,
  `warga_id` INT NOT NULL,
  `status_sesi` ENUM('berlangsung', 'terjawab', 'dieskalasi', 'selesai') NOT NULL DEFAULT 'berlangsung',
  `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `ended_at` DATETIME NULL,
  CONSTRAINT `fk_session_warga` FOREIGN KEY (`warga_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `chat_messages` (
  `message_id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` INT NOT NULL,
  `pengirim` ENUM('warga', 'sistem_ai', 'rt') NOT NULL,
  `isi_pesan` TEXT NOT NULL,
  `top_chunk_id` INT NULL,
  `similarity_score` DECIMAL(5, 4) NULL,
  `waktu_kirim` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_message_session` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_message_chunk` FOREIGN KEY (`top_chunk_id`) REFERENCES `knowledge_chunks` (`chunk_id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 6. TABEL NOTIFIKASI
CREATE TABLE IF NOT EXISTS `notifikasi` (
  `notifikasi_id` INT AUTO_INCREMENT PRIMARY KEY,
  `penerima_id` INT NOT NULL,
  `tipe_notifikasi` ENUM('pengajuan_baru', 'perlu_revisi', 'surat_disetujui', 'surat_ditolak', 'surat_siap_diambil', 'eskalasi_chat') NOT NULL,
  `judul` VARCHAR(100) NOT NULL,
  `pesan_notifikasi` VARCHAR(255) NOT NULL,
  `tautan_tujuan` VARCHAR(255) NULL,
  `is_dibaca` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_notifikasi_user` FOREIGN KEY (`penerima_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB;
