# Database Management & Connection Layer

## Overview
Database connectivity, connection pooling, schema migrations, and master data seeding subsystem for RTConnect. Manages PostgreSQL/Supabase database connections using `psycopg` and `psycopg_pool`, provides standardized query helpers returning dictionary records, and coordinates master data initialization and maintenance scripts.

## Interface
- `db.py`: Connection pooling and transaction execution helpers.
  - `get_pool() -> ConnectionPool`: Retrieves or initializes the thread-safe connection pool singleton.
  - `close_pool() -> None`: Shuts down the active connection pool.
  - `query_all(sql: str, params: tuple | dict = None) -> list[dict]`: Executes SQL SELECT and returns all matching rows as dictionaries.
  - `query_one(sql: str, params: tuple | dict = None) -> dict | None`: Executes SQL SELECT and returns a single dictionary row or None.
  - `execute(sql: str, params: tuple | dict = None) -> int`: Executes INSERT/UPDATE/DELETE statement and returns affected row count.
  - `execute_returning(sql: str, params: tuple | dict = None) -> dict | None`: Executes DML with a `RETURNING` clause and returns the resulting dictionary.
  - `transaction()`: Context manager wrapping database queries in a single atomic transaction block with automatic commit/rollback.
- `migrate.py`:
  - `migrate() -> None`: Applies pending migrations to bring the database schema up to date.
- `seed.py`:
  - `seed_database(include_demo_users: bool = None) -> None`: Idempotently seeds master letter types and 20 public administration knowledge chunks from `chatbot/dataset/knowledgebase.jsonl`.
- `create_rt_user.py`: Interactive CLI to provision the initial RT account with secure bcrypt hashing.
- `hash_rt_pin.py`: CLI generator producing bcrypt hash strings for `RT_SIGNING_PIN_HASH`.
- `sync_local_uploads_to_s3.py`: Batch utility migrating local upload files to S3-compatible object storage.
- `backfill_embeddings.py`: Migration utility to calculate and persist embedding representations for knowledge chunks.
- Subdirectories:
  - [./supabase_sql/README.md](./supabase_sql/README.md) - PostgreSQL / Supabase incremental migration scripts and DDL definitions.

## Invariants
- Connection string validation: Requires `SUPABASE_DB_URL`, `DATABASE_URL`, or `POSTGRES_URL` in environment configuration; fails fast if none is provided.
- Thread-safe lifecycle: Connection pool instantiation is locked via `threading.Lock` to guarantee a single pool instance across concurrent request threads.
- Production guard: Demo user seeding is strictly disallowed when `APP_ENV=production`.
- Transaction boundaries: `transaction()` context managers guarantee that unhandled exceptions trigger an automatic rollback before releasing the connection.

## Side Effects
- Opens and closes TCP/TLS socket connections to PostgreSQL / Supabase server.
- Modifies database state via DDL (migrations) and DML (application queries, seeding).
- Reads local filesystem files (`chatbot/dataset/knowledgebase.jsonl`, local uploads) and performs network I/O to object storage during S3 synchronization.

## Verification
- Run: `cd backend && python test_api.py`
- Migration test: `cd backend && python -m database.migrate`
- Seed test: `cd backend && python -m database.seed`
