# Supabase PostgREST Client & Repository Layer

## Overview
PostgREST client abstraction and Repository pattern implementation for Supabase integration. Exposes type-safe repositories for all domain models, manages singleton HTTP clients using Supabase service role and anon keys, and provides Flask health integration and schema introspection tools.

## Interface
- `client.py`: Supabase HTTP client manager.
  - `get_supabase() -> Client`: Returns cached service-role Supabase client instance.
  - `get_anon_supabase() -> Client`: Returns cached anonymous client instance.
  - `reset_clients() -> None`: Clears cached client singletons.
- `config.py`: Environment configuration parser.
  - `get_settings() -> SupabaseSettings`: Loads and validates `SUPABASE_URL` and keys from `.env`.
- `base_repository.py`: Generic CRUD operations over Supabase tables.
  - `BaseRepository.find_all(filters, limit, offset, order_by) -> list[dict]`: Queries table with filtering.
  - `BaseRepository.find_by_id(id) -> dict | None`: Queries single record by primary key.
  - `BaseRepository.insert(data) -> dict`: Inserts record and returns created row.
  - `BaseRepository.update(id, data) -> dict`: Updates record by ID.
  - `BaseRepository.delete(id) -> bool`: Deletes record by ID.
- `repositories.py`: Concrete entity repositories.
  - `WargaRepository`, `RTRepository`, `PengajuanSuratRepository`, `DraftSuratRepository`, `SuratFinalRepository`, `JenisSuratRepository`, `NotifikasiRepository`, `ChatSessionRepository`, `ChatMessageRepository`, `KnowledgeChunkRepository`.
- `tables.py`: `Tables` constants mapping canonical table identifiers.
- `health.py`:
  - `check_connection() -> dict`: Performs live round-trip test to Supabase.
  - `check_all_tables() -> dict[str, dict]`: Verifies accessibility and row counts across all managed tables.
- `flask_integration.py`:
  - `init_supabase(app: Flask) -> None`: Mounts `/api/v1/supabase/health` diagnostic route.
- `errors.py`: Exception classes (`SupabaseConnectError`, `SupabaseConfigError`, `SupabaseQueryError`).

## Invariants
- Credential requirements: `SUPABASE_URL` and a valid service role key (`SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY`) must be set; invalid URLs raise `SupabaseConfigError` immediately on client instantiation.
- Singleton consistency: `get_supabase()` lazily instantiates and caches a single client session per process unless explicitly reset with `reset_clients()`.
- Data serialization: `_jsonable` transforms dates, times, and non-primitive values into ISO strings prior to transmitting requests to PostgREST.

## Side Effects
- Outbound HTTPS network calls to Supabase REST endpoints (`https://<project-ref>.supabase.co/rest/v1/*`).
- Reads configuration from `.env` files.
- Executes remote CRUD operations modifying state in Supabase database tables.

## Verification
- Run: `cd backend && python test_api.py`
- Test connection: `cd backend && python -m supabase_connect.test_connection`
- Schema check: `cd backend && python -m supabase_connect.inspect_schema`
