# Supabase & PostgreSQL Migration Scripts

## Overview
SQL migration scripts defining the relational schema, ENUM definitions, extensions, and schema patches for PostgreSQL and Supabase environments. These migrations establish the canonical database structure used during CI pipeline tests, Supabase remote environments, and automated setup scripts (`setup_supabase.py`).

## Interface
- `000_base_schema.sql`: Foundational DDL defining ENUMs (`pengirim_enum`, `status_surat_enum`, `peran_enum`, etc.) and core tables (`warga`, `rt`, `pengajuansurat`, `jenis_surat`, `notifikasi`, `sesi_chat`, `pesan_chat`).
- `001_enums.sql`: Idempotent migration registering additional enum values for chat senders and session statuses.
- `002_extensions.sql`: Feature extension migration adding columns for official letter numbering (`nomor_surat_resmi`), digital signatures (`qr_verifikasi`, `pin_hash`), attachments, and push notification metadata.
- `003_data_pemohon.sql`: Schema addition adding snapshot demographic columns (`pekerjaan`, `jenis_kelamin`, `tempat_lahir`, `tanggal_lahir`, `agama`, `status_kawin`) to `pengajuansurat`.
- `004_alamat_surabaya.sql`: Administrative boundary update setting defaults for RT 04 / RW 09 Gunungsari Indah, Kelurahan Kedurus, Karang Pilang, Surabaya.
- `005_ai_fill_log.sql`: Creates `ai_fill_log` table for tracking accuracy, timing, and resident edits during AI form pre-filling.
- `006_fcm_tokens.sql`: Adds `fcm_token` and timestamp tracking with indexes to `warga` and `rt` tables for Firebase Cloud Messaging.

## Invariants
- Idempotency: All scripts must be safe to execute multiple times against existing databases without errors (using `IF NOT EXISTS`, exception handlers on type creation, or safe column checks).
- Non-destructive evolution: Migrations only perform additive schema updates (`ADD COLUMN`, `ALTER DEFAULT`, `CREATE TABLE`); destructive drops of production columns are prohibited.
- Schema parity: The PostgreSQL schema declared across these files must reflect the business logic implemented in the backend application and API routes.

## Side Effects
- Modifies remote or local PostgreSQL database schemas by executing DDL statements (creates tables, adds columns, indexes, and ENUM values).

## Verification
- Run: `cd backend && python test_api.py`
- Supabase setup check: `cd backend && python setup_supabase.py`
