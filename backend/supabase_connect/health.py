"""Pengecekan koneksi & ketersediaan tabel."""

from __future__ import annotations

import time

from .errors import SupabaseConnectError
from .repositories import REPOSITORY_CLASSES
from .tables import ALL_TABLES, Tables


def check_connection() -> dict:
    """Ping ringan ke Supabase. Tidak melempar exception; hasil ada di dict."""
    started = time.perf_counter()
    try:
        REPOSITORY_CLASSES[Tables.JENIS_SURAT]().list(limit=1)
        return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1), "error": None}
    except SupabaseConnectError as exc:
        return {"ok": False, "latency_ms": round((time.perf_counter() - started) * 1000, 1), "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "latency_ms": None, "error": f"{type(exc).__name__}: {exc}"}


def check_all_tables() -> dict[str, dict]:
    report: dict[str, dict] = {}
    for table in ALL_TABLES:
        try:
            report[table] = {"ok": True, "rows": REPOSITORY_CLASSES[table]().count(), "error": None}
        except SupabaseConnectError as exc:
            report[table] = {"ok": False, "rows": None, "error": str(exc)}
    return report