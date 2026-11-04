"""Membaca struktur tabel (kolom, tipe, PK, FK) dari OpenAPI Data API Supabase.

Catatan: Supabase biasanya hanya mengizinkan pembacaan skema dengan service key.
Kalau gagal, deteksi primary key otomatis diabaikan (fallback ke kolom 'id'
atau nilai `primary_key` yang Anda isi di repository).
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field

import httpx

from .config import get_settings
from .errors import SupabaseQueryError

_PK_MARK = "<pk/>"
_FK_RE = re.compile(r"<fk table='([^']+)' column='([^']+)'/>")


@dataclass
class ColumnInfo:
    name: str
    type: str
    format: str | None = None
    required: bool = False
    primary_key: bool = False
    default: object | None = None
    references: str | None = None


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)

    @property
    def primary_key(self) -> list[str]:
        return [c.name for c in self.columns if c.primary_key]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


_cache: dict[str, TableInfo] | None = None
_cache_lock = threading.Lock()


def _parse(spec: dict) -> dict[str, TableInfo]:
    tables: dict[str, TableInfo] = {}
    for table_name, definition in (spec.get("definitions") or {}).items():
        required = set(definition.get("required") or [])
        info = TableInfo(name=table_name)
        for col_name, col in (definition.get("properties") or {}).items():
            description = col.get("description") or ""
            fk = _FK_RE.search(description)
            info.columns.append(
                ColumnInfo(
                    name=col_name,
                    type=col.get("type", "unknown"),
                    format=col.get("format"),
                    required=col_name in required,
                    primary_key=_PK_MARK in description,
                    default=col.get("default"),
                    references=f"{fk.group(1)}.{fk.group(2)}" if fk else None,
                )
            )
        tables[table_name] = info
    return tables


def fetch_schema(force: bool = False) -> dict[str, TableInfo]:
    global _cache
    if _cache is not None and not force:
        return _cache
    with _cache_lock:
        if _cache is not None and not force:
            return _cache
        settings = get_settings()
        key = settings.client_key()

        # Key format baru (sb_secret_... / sb_publishable_...) bukan JWT:
        # hanya header 'apikey' yang boleh dipakai. Key lama (eyJ...) butuh Bearer juga.
        headers = {"apikey": key, "Accept-Profile": settings.schema}
        if key.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {key}"

        try:
            response = httpx.get(
                f"{settings.rest_url}/",
                headers=headers,
                timeout=settings.timeout,
            )
            response.raise_for_status()
            _cache = _parse(response.json())
        except httpx.HTTPStatusError as exc:
            raise SupabaseQueryError(
                f"Gagal membaca skema (HTTP {exc.response.status_code}). "
                "Pembacaan skema umumnya butuh service key.",
                operation="schema",
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise SupabaseQueryError(f"Gagal menghubungi Supabase: {exc}", operation="schema") from exc
        return _cache


def get_primary_key(table: str) -> str | None:
    try:
        info = fetch_schema().get(table)
    except SupabaseQueryError:
        return None
    if info and info.primary_key:
        return info.primary_key[0]
    return None


def clear_schema_cache() -> None:
    global _cache
    with _cache_lock:
        _cache = None