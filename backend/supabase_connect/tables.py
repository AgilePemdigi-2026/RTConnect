"""Daftar tabel Supabase RTConnect."""

from __future__ import annotations


class Tables:
    CHAT_MESSAGE = "chatmessage"
    CHAT_SESSION = "chatsession"
    DRAFT_SURAT = "draftsurat"
    JENIS_SURAT = "jenissurat"
    KNOWLEDGE_BASE = "knowledgebase"
    KNOWLEDGE_CHUNK = "knowledgechunk"
    NOTIFIKASI = "notifikasi"
    PENGAJUAN_SURAT = "pengajuansurat"
    RETRIEVAL_LOG = "retrievallog"
    RT = "rt"
    SURAT_FINAL = "suratfinal"
    WARGA = "warga"


ALL_TABLES: tuple[str, ...] = (
    Tables.CHAT_MESSAGE, Tables.CHAT_SESSION, Tables.DRAFT_SURAT, Tables.JENIS_SURAT,
    Tables.KNOWLEDGE_BASE, Tables.KNOWLEDGE_CHUNK, Tables.NOTIFIKASI, Tables.PENGAJUAN_SURAT,
    Tables.RETRIEVAL_LOG, Tables.RT, Tables.SURAT_FINAL, Tables.WARGA,
)

# Tabel MySQL lama -> tabel Supabase (DUGAAN dari kemiripan nama; cocokkan dulu dengan kolom asli).
LEGACY_MYSQL_TO_SUPABASE: dict[str, tuple[str, ...]] = {
    "users": (Tables.WARGA, Tables.RT),
    "jenis_surat": (Tables.JENIS_SURAT,),
    "pengajuan_surat": (Tables.PENGAJUAN_SURAT, Tables.DRAFT_SURAT),
    "surat_final": (Tables.SURAT_FINAL,),
    "knowledge_base": (Tables.KNOWLEDGE_BASE,),
    "knowledge_chunks": (Tables.KNOWLEDGE_CHUNK,),
    "chat_sessions": (Tables.CHAT_SESSION,),
    "chat_messages": (Tables.CHAT_MESSAGE, Tables.RETRIEVAL_LOG),
    "notifikasi": (Tables.NOTIFIKASI,),
}