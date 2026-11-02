"""Uji koneksi. Jalankan dari backend/:  python -m supabase_connect.test_connection"""

from __future__ import annotations

import sys

from .config import get_settings
from .errors import SupabaseConnectError
from .health import check_all_tables, check_connection


def main() -> int:
    try:
        settings = get_settings()
        settings.client_key()
    except SupabaseConnectError as exc:
        print(f"[GAGAL] Konfigurasi: {exc}")
        return 2

    print(f"Project : {settings.project_ref}")
    print(f"Schema  : {settings.schema}")
    key = settings.client_key()
    if key.startswith("sb_secret_"):
        jenis = "secret (melewati RLS)"
    elif key.startswith("sb_publishable_"):
        jenis = "PUBLISHABLE (tunduk RLS, hasil 0 baris belum tentu kosong)"
    else:
        jenis = "JWT lama (cek di dashboard apakah role-nya service_role)"
    print(f"Key     : {jenis}\n")
    ping = check_connection()
    if not ping["ok"]:
        print(f"[GAGAL] Tidak bisa terhubung: {ping['error']}")
        return 1
    print(f"[OK] Terhubung ({ping['latency_ms']} ms)\n")

    report = check_all_tables()
    width = max(len(t) for t in report)
    failed = 0
    for table, info in report.items():
        if info["ok"]:
            print(f"  [OK]    {table:<{width}}  {info['rows']} baris")
        else:
            failed += 1
            print(f"  [GAGAL] {table:<{width}}  {info['error']}")
    print()
    if failed:
        print(f"{failed} tabel bermasalah. Penyebab umum: nama tabel beda, RLS aktif tanpa policy "
              f"(kode 42501 / hasil kosong), atau tabel tidak ada di schema '{settings.schema}'.")
        return 1
    print("Semua tabel dapat diakses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())