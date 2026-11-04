"""Pembuat client Supabase (singleton, aman dipakai di banyak thread Gunicorn)."""

from __future__ import annotations

import threading

from supabase import Client, ClientOptions, create_client

from .config import get_settings
from .errors import SupabaseConnectError

_lock = threading.Lock()
_main_client: Client | None = None
_anon_client: Client | None = None


def _options() -> ClientOptions:
    settings = get_settings()
    return ClientOptions(
        schema=settings.schema,
        auto_refresh_token=False,
        persist_session=False,
        postgrest_client_timeout=settings.timeout,
    )


def get_supabase() -> Client:
    """Client utama backend.

    Memakai SUPABASE_SERVICE_ROLE_KEY bila diisi di .env (melewati RLS),
    kalau tidak memakai publishable key (tunduk pada RLS).
    """
    global _main_client
    if _main_client is None:
        with _lock:
            if _main_client is None:
                settings = get_settings()
                try:
                    _main_client = create_client(settings.url, settings.client_key(), options=_options())
                except SupabaseConnectError:
                    raise
                except Exception as exc:
                    raise SupabaseConnectError(f"Gagal membuat client Supabase: {exc}") from exc
    return _main_client


def get_anon_supabase() -> Client:
    """Client dengan publishable/anon key (selalu tunduk pada RLS)."""
    global _anon_client
    if _anon_client is None:
        with _lock:
            if _anon_client is None:
                settings = get_settings()
                try:
                    _anon_client = create_client(settings.url, settings.require_anon_key(), options=_options())
                except SupabaseConnectError:
                    raise
                except Exception as exc:
                    raise SupabaseConnectError(f"Gagal membuat client Supabase (anon): {exc}") from exc
    return _anon_client


def reset_clients() -> None:
    global _main_client, _anon_client
    with _lock:
        _main_client = None
        _anon_client = None