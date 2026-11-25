# EGM Drift Report - 2026-11-24

This report evaluates design contracts and documentation against the actual codebase implementation across RTConnect.

## README.md
- **Database Engine Dual-Stack Divergence**: The architectural overview references MySQL 8.0/8.4, whereas the backend implementation includes PostgreSQL / Supabase migrations (`backend/database/supabase_sql/`, `backend/supabase_connect/`) and `psycopg-pool` alongside MySQL.
- **Letter Submission Pipeline Divergence**: Legacy documentation sections reference `lib/features/pengajuan_rt/` with endpoints `/api/rt/pengajuan`, whereas production resident and RT letter processing is implemented in `frontend/lib/features/letters/` connecting to `/api/v1/letters`.

## backend/README.md
- **Database Connection Dual-Stack Divergence**: Documentation notes MySQL / PyMySQL in stack details, but dependencies and migrations include `psycopg[binary]`, `psycopg-pool`, and Supabase SQL patches in `database/supabase_sql/`.

## backend/chatbot/README.md
No drift detected.

## backend/database/README.md
No drift detected.

## backend/database/supabase_sql/README.md
No drift detected.

## backend/features/README.md
No drift detected.

## backend/features/steps/README.md
No drift detected.

## backend/middleware/README.md
No drift detected.

## backend/routes/README.md
No drift detected.

## backend/services/README.md
No drift detected.

## backend/supabase_connect/README.md
No drift detected.

## frontend/README.md
No drift detected.

## frontend/lib/README.md
No drift detected.

## frontend/lib/core/README.md
No drift detected.

## frontend/lib/core/constants/README.md
No drift detected.

## frontend/lib/core/errors/README.md
No drift detected.

## frontend/lib/core/network/README.md
No drift detected.

## frontend/lib/core/router/README.md
No drift detected.

## frontend/lib/core/services/README.md
No drift detected.

## frontend/lib/core/theme/README.md
No drift detected.

## frontend/lib/features/README.md
No drift detected.

## frontend/lib/features/auth/README.md
No drift detected.

## frontend/lib/features/auth/data/README.md
No drift detected.

## frontend/lib/features/auth/domain/README.md
No drift detected.

## frontend/lib/features/auth/presentation/README.md
No drift detected.

## frontend/lib/features/chatbot/README.md
No drift detected.

## frontend/lib/features/chatbot/data/README.md
No drift detected.

## frontend/lib/features/chatbot/presentation/README.md
No drift detected.

## frontend/lib/features/home/README.md
No drift detected.

## frontend/lib/features/home/presentation/README.md
No drift detected.

## frontend/lib/features/letters/README.md
No drift detected.

## frontend/lib/features/letters/data/README.md
No drift detected.

## frontend/lib/features/letters/presentation/README.md
No drift detected.

## frontend/lib/features/letters/presentation/widgets/README.md
No drift detected.

## frontend/lib/features/notifications/README.md
No drift detected.

## frontend/lib/features/notifications/data/README.md
No drift detected.

## frontend/lib/features/notifications/presentation/README.md
No drift detected.

## frontend/lib/features/pengajuan_rt/README.md
- **Demo vs Production Divergence**: Documents standalone demo architecture and mock endpoints (`/api/rt/pengajuan`) for `lib/main_demo_rt.dart`. Production letter flows operate on `/api/v1/letters`.

## frontend/lib/features/pengajuan_rt/models/README.md
No drift detected.

## frontend/lib/features/pengajuan_rt/pages/README.md
No drift detected.

## frontend/lib/features/pengajuan_rt/services/README.md
No drift detected.

## frontend/lib/features/pengajuan_rt/widgets/README.md
No drift detected.

## frontend/lib/features/profile/README.md
No drift detected.

## frontend/lib/features/profile/data/README.md
No drift detected.

## frontend/lib/features/profile/presentation/README.md
No drift detected.

## frontend/lib/shared/README.md
No drift detected.

## frontend/lib/shared/widgets/README.md
No drift detected.
