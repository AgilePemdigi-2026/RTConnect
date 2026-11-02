"""Konfigurasi Supabase RTConnect.

URL project dan publishable key sudah tertulis di bawah, jadi tidak wajib ada file .env.
Kalau ingin menimpa, isi variabel di .env:
  SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY (atau SUPABASE_ANON_KEY),
  SUPABASE_SERVICE_ROLE_KEY (opsional, RAHASIA, melewati RLS), SUPABASE_SCHEMA, SUPABASE_TIMEOUT
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from .errors import SupabaseConfigError

_PACKAGE_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _PACKAGE_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent

for _env_file in (_PACKAGE_DIR / ".env", _BACKEND_DIR / ".env", _ROOT_DIR / ".env"):
    load_dotenv(_env_file)
load_dotenv()

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

# ---- Nilai bawaan project RTConnect ---------------------------------------
DEFAULT_SUPABASE_URL = "https://okmubevurpbgcckoclym.supabase.co"
# Publishable key bersifat publik (aman ditulis di kode).
# JANGAN pernah menulis service_role / sb_secret_... di file ini.
DEFAULT_PUBLISHABLE_KEY = "sb_publishable_SFQsVkq2KpAFrdI7oxyk_A_jFRmm06V"
# ---------------------------------------------------------------------------


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _normalize_url(raw: str) -> str:
    url = raw.strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SupabaseConfigError(
            "SUPABASE_URL tidak valid. Contoh yang benar: https://<project-ref>.supabase.co"
        )
    if parsed.scheme == "http" and parsed.hostname not in _LOCAL_HOSTS:
        raise SupabaseConfigError("SUPABASE_URL harus memakai https (http hanya boleh untuk localhost).")
    return url


@dataclass(frozen=True)
class SupabaseSettings:
    url: str
    service_role_key: str | None = field(default=None, repr=False)
    anon_key: str | None = field(default=None, repr=False)
    schema: str = "public"
    timeout: float = 30.0

    @property
    def rest_url(self) -> str:
        return f"{self.url}/rest/v1"

    @property
    def project_ref(self) -> str:
        host = urlparse(self.url).hostname or ""
        return host.split(".")[0]

    def require_service_key(self) -> str:
        if not self.service_role_key:
            raise SupabaseConfigError(
                "SUPABASE_SERVICE_ROLE_KEY belum diisi. Ambil dari Dashboard Supabase > "
                "Project Settings > API Keys, lalu taruh di .env backend (jangan di kode / Flutter)."
            )
        return self.service_role_key

    def require_anon_key(self) -> str:
        if not self.anon_key:
            raise SupabaseConfigError("Publishable/anon key belum tersedia.")
        return self.anon_key

    def client_key(self) -> str:
        """Pakai service key bila ada, kalau tidak pakai publishable key."""
        key = self.service_role_key or self.anon_key
        if not key:
            raise SupabaseConfigError("Belum ada API key Supabase (service key maupun publishable key).")
        return key


@lru_cache(maxsize=1)
def get_settings() -> SupabaseSettings:
    raw_url = _first_env("SUPABASE_URL")
    if not raw_url:
        ref = _first_env("SUPABASE_PROJECT_REF")
        raw_url = f"https://{ref}.supabase.co" if ref else DEFAULT_SUPABASE_URL

    try:
        timeout = float(_first_env("SUPABASE_TIMEOUT") or 30)
    except ValueError as exc:
        raise SupabaseConfigError("SUPABASE_TIMEOUT harus berupa angka (detik).") from exc

    return SupabaseSettings(
        url=_normalize_url(raw_url),
        service_role_key=_first_env("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEY", "SUPABASE_KEY"),
        anon_key=_first_env("SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEY") or DEFAULT_PUBLISHABLE_KEY,
        schema=_first_env("SUPABASE_SCHEMA") or "public",
        timeout=timeout,
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()