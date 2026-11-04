"""supabase_connect - jembatan antara backend Flask RTConnect dan Supabase (PostgreSQL)."""

from .base_repository import BaseRepository
from .client import get_anon_supabase, get_supabase, reset_clients
from .config import SupabaseSettings, get_settings
from .errors import SupabaseConfigError, SupabaseConnectError, SupabaseQueryError
from .health import check_all_tables, check_connection
from .repositories import REPOSITORY_CLASSES, repos
from .schema import fetch_schema
from .tables import ALL_TABLES, LEGACY_MYSQL_TO_SUPABASE, Tables

__all__ = [
    "ALL_TABLES", "BaseRepository", "LEGACY_MYSQL_TO_SUPABASE", "REPOSITORY_CLASSES",
    "SupabaseConfigError", "SupabaseConnectError", "SupabaseQueryError", "SupabaseSettings",
    "Tables", "check_all_tables", "check_connection", "fetch_schema", "get_anon_supabase",
    "get_settings", "get_supabase", "repos", "reset_clients",
]