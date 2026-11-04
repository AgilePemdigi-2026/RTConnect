"""Tampilkan kolom, tipe, PK & FK semua tabel Supabase (umumnya butuh service key).

    python -m supabase_connect.inspect_schema
    python -m supabase_connect.inspect_schema --json skema.json
    python -m supabase_connect.inspect_schema warga rt
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .errors import SupabaseConnectError
from .schema import fetch_schema
from .tables import ALL_TABLES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tables", nargs="*", help="Nama tabel (default: 12 tabel RTConnect)")
    parser.add_argument("--json", metavar="FILE", help="Simpan hasil ke file JSON")
    args = parser.parse_args()

    try:
        schema = fetch_schema(force=True)
    except SupabaseConnectError as exc:
        print(f"[GAGAL] {exc}")
        return 1

    out: dict[str, dict] = {}
    for name in (args.tables or list(ALL_TABLES)):
        info = schema.get(name)
        if info is None:
            print(f"\n== {name}: TIDAK DITEMUKAN di Data API (cek nama tabel / schema / hak akses)")
            continue
        out[name] = {"primary_key": info.primary_key, "columns": [asdict(c) for c in info.columns]}
        print(f"\n== {name}   (PK: {', '.join(info.primary_key) or '-'})")
        for c in info.columns:
            flags = []
            if c.primary_key: flags.append("PK")
            if c.required: flags.append("NOT NULL")
            if c.references: flags.append(f"FK -> {c.references}")
            if c.default is not None: flags.append(f"default={c.default}")
            print(f"   {c.name:<28} {c.format or c.type:<26} {' '.join(flags)}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        print(f"\nDisimpan ke {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())