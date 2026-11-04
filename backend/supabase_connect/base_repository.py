"""Repository generik (CRUD) di atas supabase-py.

Format filter (dict {kolom: kondisi}):
    {"status": "diajukan"}                 -> status = 'diajukan'
    {"rt_id": None}                        -> rt_id IS NULL
    {"id": ("in", [1, 2, 3])}              -> id IN (1,2,3)
    {"id": ("not_in", [1, 2])}             -> id NOT IN (1,2)
    {"created_at": ("gte", "2026-01-01")}  -> created_at >= ...
    {"nama": ("ilike", "%budi%")}          -> nama ILIKE '%budi%'
"""

from __future__ import annotations

import datetime as _dt
import decimal
import uuid
from typing import Any, Iterable, Mapping

from postgrest.exceptions import APIError

from .client import get_supabase
from .errors import SupabaseQueryError
from .schema import get_primary_key

Filters = Mapping[str, Any]


def _jsonable(value: Any) -> Any:
    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


def _apply_filters(query, filters: Filters | None):
    for column, condition in (filters or {}).items():
        if isinstance(condition, tuple):
            if len(condition) != 2:
                raise ValueError(f"Filter '{column}' harus berbentuk (operator, nilai).")
            op, value = condition
            value = _jsonable(value)
            if op == "in":
                query = query.in_(column, list(value))
            elif op == "not_in":
                query = query.not_.in_(column, list(value))
            elif op == "is":
                query = query.is_(column, value)
            else:
                query = query.filter(column, op, value)
        elif condition is None:
            query = query.is_(column, "null")
        else:
            query = query.eq(column, _jsonable(condition))
    return query


class BaseRepository:
    table: str = ""                 # wajib diisi subclass
    primary_key: str | None = None  # None = deteksi otomatis, fallback 'id'

    def __init__(self, client=None):
        if not self.table:
            raise TypeError(f"{type(self).__name__} belum menentukan atribut 'table'.")
        self._client = client

    @property
    def client(self):
        return self._client or get_supabase()

    @property
    def pk(self) -> str:
        return self.primary_key or get_primary_key(self.table) or "id"

    def _query(self):
        return self.client.table(self.table)

    def _run(self, operation: str, builder):
        try:
            return builder.execute()
        except APIError as exc:
            raise SupabaseQueryError(
                exc.message or "Query Supabase gagal",
                code=exc.code, details=exc.details, hint=exc.hint,
                table=self.table, operation=operation,
            ) from exc
        except SupabaseQueryError:
            raise
        except Exception as exc:
            raise SupabaseQueryError(
                f"{type(exc).__name__}: {exc}", table=self.table, operation=operation
            ) from exc

    # ---- read ----
    def list(self, *, filters: Filters | None = None, columns: str = "*",
             order_by: str | None = None, desc: bool = False,
             limit: int | None = None, offset: int = 0) -> list[dict]:
        query = _apply_filters(self._query().select(columns), filters)
        if order_by:
            query = query.order(order_by, desc=desc)
        if limit is not None:
            query = query.range(offset, offset + limit - 1)
        elif offset:
            query = query.range(offset, offset + 999)
        return self._run("select", query).data or []

    def get(self, pk_value: Any, columns: str = "*") -> dict | None:
        rows = self.list(filters={self.pk: pk_value}, columns=columns, limit=1)
        return rows[0] if rows else None

    def find_one(self, filters: Filters, columns: str = "*", order_by: str | None = None,
                 desc: bool = False) -> dict | None:
        rows = self.list(filters=filters, columns=columns, order_by=order_by, desc=desc, limit=1)
        return rows[0] if rows else None

    def exists(self, filters: Filters) -> bool:
        return self.find_one(filters) is not None

    def count(self, filters: Filters | None = None) -> int:
        query = _apply_filters(self._query().select("*", count="exact"), filters).limit(1)
        return self._run("count", query).count or 0

    # ---- write ----
    def insert(self, data: Mapping[str, Any] | Iterable[Mapping[str, Any]]):
        many = not isinstance(data, Mapping)
        payload = [_jsonable(d) for d in data] if many else _jsonable(data)
        rows = self._run("insert", self._query().insert(payload)).data or []
        return rows if many else (rows[0] if rows else {})

    def update(self, pk_value: Any, data: Mapping[str, Any]) -> dict | None:
        rows = self.update_where({self.pk: pk_value}, data)
        return rows[0] if rows else None

    def update_where(self, filters: Filters, data: Mapping[str, Any]) -> list[dict]:
        if not filters:
            raise ValueError("update_where tanpa filter ditolak agar tidak mengubah seluruh tabel.")
        query = _apply_filters(self._query().update(_jsonable(data)), filters)
        return self._run("update", query).data or []

    def upsert(self, data: Mapping[str, Any] | Iterable[Mapping[str, Any]],
               on_conflict: str | None = None):
        many = not isinstance(data, Mapping)
        payload = [_jsonable(d) for d in data] if many else _jsonable(data)
        builder = (self._query().upsert(payload, on_conflict=on_conflict) if on_conflict
                   else self._query().upsert(payload))
        rows = self._run("upsert", builder).data or []
        return rows if many else (rows[0] if rows else {})

    def delete(self, pk_value: Any) -> bool:
        return bool(self.delete_where({self.pk: pk_value}))

    def delete_where(self, filters: Filters) -> list[dict]:
        if not filters:
            raise ValueError("delete_where tanpa filter ditolak agar tidak menghapus seluruh tabel.")
        query = _apply_filters(self._query().delete(), filters)
        return self._run("delete", query).data or []