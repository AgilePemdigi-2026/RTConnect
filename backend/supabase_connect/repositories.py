"""Satu repository per tabel Supabase. Contoh: repos.warga.list(filters={...})

Kalau primary key tabel bukan 'id' dan tidak terdeteksi otomatis, isi manual,
misalnya di WargaRepository tambahkan:  primary_key = "warga_id"
"""

from __future__ import annotations

from functools import cached_property

from .base_repository import BaseRepository
from .tables import Tables


class ChatMessageRepository(BaseRepository):
    table = Tables.CHAT_MESSAGE

class ChatSessionRepository(BaseRepository):
    table = Tables.CHAT_SESSION

class DraftSuratRepository(BaseRepository):
    table = Tables.DRAFT_SURAT

class JenisSuratRepository(BaseRepository):
    table = Tables.JENIS_SURAT

class KnowledgeBaseRepository(BaseRepository):
    table = Tables.KNOWLEDGE_BASE

class KnowledgeChunkRepository(BaseRepository):
    table = Tables.KNOWLEDGE_CHUNK

class NotifikasiRepository(BaseRepository):
    table = Tables.NOTIFIKASI

class PengajuanSuratRepository(BaseRepository):
    table = Tables.PENGAJUAN_SURAT

class RetrievalLogRepository(BaseRepository):
    table = Tables.RETRIEVAL_LOG

class RTRepository(BaseRepository):
    table = Tables.RT

class SuratFinalRepository(BaseRepository):
    table = Tables.SURAT_FINAL

class WargaRepository(BaseRepository):
    table = Tables.WARGA


REPOSITORY_CLASSES: dict[str, type[BaseRepository]] = {
    cls.table: cls
    for cls in (
        ChatMessageRepository, ChatSessionRepository, DraftSuratRepository,
        JenisSuratRepository, KnowledgeBaseRepository, KnowledgeChunkRepository,
        NotifikasiRepository, PengajuanSuratRepository, RetrievalLogRepository,
        RTRepository, SuratFinalRepository, WargaRepository,
    )
}


class _Repositories:
    """Akses lazy: repos.warga, repos.rt, dst."""

    @cached_property
    def chat_message(self): return ChatMessageRepository()
    @cached_property
    def chat_session(self): return ChatSessionRepository()
    @cached_property
    def draft_surat(self): return DraftSuratRepository()
    @cached_property
    def jenis_surat(self): return JenisSuratRepository()
    @cached_property
    def knowledge_base(self): return KnowledgeBaseRepository()
    @cached_property
    def knowledge_chunk(self): return KnowledgeChunkRepository()
    @cached_property
    def notifikasi(self): return NotifikasiRepository()
    @cached_property
    def pengajuan_surat(self): return PengajuanSuratRepository()
    @cached_property
    def retrieval_log(self): return RetrievalLogRepository()
    @cached_property
    def rt(self): return RTRepository()
    @cached_property
    def surat_final(self): return SuratFinalRepository()
    @cached_property
    def warga(self): return WargaRepository()

    def by_table(self, table_name: str) -> BaseRepository:
        try:
            return REPOSITORY_CLASSES[table_name]()
        except KeyError as exc:
            raise KeyError(f"Tabel '{table_name}' tidak dikenal. Pilihan: {sorted(REPOSITORY_CLASSES)}") from exc


repos = _Repositories()