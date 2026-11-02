from __future__ import annotations


class SupabaseConnectError(RuntimeError):
    """Kelas dasar untuk semua error dari paket supabase_connect."""


class SupabaseConfigError(SupabaseConnectError):
    """Konfigurasi belum lengkap atau salah."""


class SupabaseQueryError(SupabaseConnectError):
    """Query ke Supabase gagal (ditolak RLS, kolom tidak ada, jaringan, dsb.)."""

    def __init__(self, message: str, *, code: str | None = None,
                 details: str | None = None, hint: str | None = None,
                 table: str | None = None, operation: str | None = None):
        super().__init__(message)
        self.code = code
        self.details = details
        self.hint = hint
        self.table = table
        self.operation = operation

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.table:
            parts.append(f"tabel={self.table}")
        if self.operation:
            parts.append(f"operasi={self.operation}")
        if self.code:
            parts.append(f"kode={self.code}")
        if self.hint:
            parts.append(f"petunjuk={self.hint}")
        return " | ".join(parts)