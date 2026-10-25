
import os
from datetime import date
from functools import lru_cache

try:
    from .retrieval import HybridRetriever
    from .rules import (
        jenis_pertanyaan,
        topik_pertanyaan,
        aksi_pertanyaan,
        coverage,
    )
except ImportError:
    from retrieval import HybridRetriever
    from rules import (
        jenis_pertanyaan,
        topik_pertanyaan,
        aksi_pertanyaan,
        coverage,
    )


PESAN = {
    "RAHASIA":
        "Saya tidak dapat membantu mengungkap PIN, "
        "OTP, kata sandi, atau informasi autentikasi.",

    "LUAR_CAKUPAN":
        "Pertanyaan tersebut berada di luar informasi "
        "administrasi yang tersedia di TanyaRT.",

    "BELUM_ADA_SOP_RT":
        "Belum tersedia SOP RT terverifikasi yang "
        "menjawab pertanyaan tersebut.",

    "PERLU_VERIFIKASI":
        "Referensi yang ditemukan belum cukup kuat "
        "untuk dijadikan jawaban pasti. "
        "Silakan periksa sumber resminya.",

    "FALLBACK":
        "Belum ditemukan referensi resmi yang "
        "sesuai dengan pertanyaan tersebut.",
}


def hasil(status, jawaban, sumber=None, skor=None):

    sumber = sumber or []

    return {
        "status": status,
        "answer": jawaban,
        "citation": (
            sumber[0]["judul"] if sumber else None
        ),
        "source_id": (
            sumber[0]["id"] if sumber else None
        ),
        "similarity_score": (
            round(float(skor), 4)
            if skor is not None else None
        ),
        "sources": sumber,
        "is_escalated": False,
        "can_escalate": status in {
            "PERLU_VERIFIKASI",
            "FALLBACK",
            "BELUM_ADA_SOP_RT"
        },
    }


def sumber_dokumen(item):

    return {
        "id": str(item["id"]),
        "judul": item["judul"],
        "url": (
            item.get("sumber")
            or item.get("url_sumber")
            or None
        )
    }


class TanyaRTService:

    def __init__(self):

        self.retriever = HybridRetriever()

        self.min_cosine = float(
            os.getenv("CHATBOT_MIN_COSINE", "0.70")
        )

        if not 0 <= self.min_cosine <= 1:
            raise ValueError(
                "CHATBOT_MIN_COSINE harus antara 0 dan 1"
            )

    def jawab_lokal(
        self,
        pertanyaan,
        rt_id,
        dokumen_lokal
    ):

        # Dokumen lokal harus berasal dari RT yang sesuai
        if rt_id is None:
            return hasil(
                "BELUM_ADA_SOP_RT",
                PESAN["BELUM_ADA_SOP_RT"]
            )

        kandidat = []

        for item in dokumen_lokal:

            if (
                str(item.get("rt_id")) != str(rt_id)
                or item.get("status_verifikasi")
                != "TERVERIFIKASI_RT"
                or not item.get("judul")
                or not item.get("konten")
            ):
                continue

            # Abaikan SOP yang masa berlakunya habis
            if (
                item.get("berlaku_sampai")
                and str(item["berlaku_sampai"])
                < date.today().isoformat()
            ):
                continue

            kandidat.append(item)

        if not kandidat:
            return hasil(
                "BELUM_ADA_SOP_RT",
                PESAN["BELUM_ADA_SOP_RT"]
            )

        teks = [
            item["judul"] + ". " + item["konten"]
            for item in kandidat
        ]

        vektor = self.retriever.model.encode(
            teks + [pertanyaan],
            normalize_embeddings=True
        )

        skor = vektor[:-1] @ vektor[-1]

        indeks = int(skor.argmax())

        cakupan = coverage(
            pertanyaan,
            teks[indeks]
        )

        # Tidak cukup hanya karena topiknya sama
        if (
            skor[indeks] < self.min_cosine
            or cakupan < 0.85
        ):
            return hasil(
                "BELUM_ADA_SOP_RT",
                PESAN["BELUM_ADA_SOP_RT"]
            )

        dokumen = kandidat[indeks]

        kutipan = " ".join(
            dokumen["konten"].split()
        )[:600]

        return hasil(
            "SUMBER_DITEMUKAN",
            (
                "Menurut SOP RT terverifikasi "
                f"'{dokumen['judul']}': {kutipan}"
            ),
            [sumber_dokumen(dokumen)],
            skor[indeks]
        )

    def jawab(
        self,
        pertanyaan,
        rt_id=None,
        dokumen_lokal=None
    ):

        pertanyaan = str(pertanyaan).strip()

        if not pertanyaan:
            return hasil(
                "PERTANYAAN_TIDAK_JELAS",
                "Pertanyaan tidak boleh kosong."
            )

        # 1. Pemeriksaan keamanan dan cakupan
        jenis = jenis_pertanyaan(pertanyaan)

        if jenis == "RAHASIA":
            return hasil(
                "RAHASIA",
                PESAN["RAHASIA"]
            )

        if jenis == "LUAR_CAKUPAN":
            return hasil(
                "LUAR_CAKUPAN",
                PESAN["LUAR_CAKUPAN"]
            )

        # 2. Pertanyaan lokal RT
        if jenis == "LOKAL_RT":
            return self.jawab_lokal(
                pertanyaan,
                rt_id,
                dokumen_lokal or []
            )

        # 3. Retrieval referensi pemerintah
        calon = self.retriever.cari(
            pertanyaan,
            top_k=3
        )

        if not calon:
            return hasil(
                "FALLBACK",
                PESAN["FALLBACK"]
            )

        topik = topik_pertanyaan(pertanyaan)
        aksi = aksi_pertanyaan(pertanyaan)

        kandidat_topik = [
            item for item in calon
            if item["topik"] == topik
        ]

        if not kandidat_topik:
            return hasil(
                "PERLU_VERIFIKASI",
                PESAN["PERLU_VERIFIKASI"]
            )

        terbaik = kandidat_topik[0]

        sumber = [
            sumber_dokumen(item)
            for item in kandidat_topik
        ]

        aksi_cocok = (
            aksi is None
            or terbaik["aksi"] is None
            or aksi == terbaik["aksi"]
        )

        # 4. Menentukan boleh tidaknya menjawab
        if (
            terbaik["skor"] >= self.min_cosine
            and aksi_cocok
        ):

            kutipan = " ".join(
                terbaik["konten"].split()
            )[:600]

            return hasil(
                "SUMBER_DITEMUKAN",
                (
                    f"Menurut sumber resmi "
                    f"'{terbaik['judul']}': {kutipan}"
                ),
                sumber,
                terbaik["skor"]
            )

        # 5. Fallback jika belum cukup kuat
        return hasil(
            "PERLU_VERIFIKASI",
            PESAN["PERLU_VERIFIKASI"],
            sumber,
            terbaik["skor"]
        )


@lru_cache(maxsize=1)
def get_service():
    return TanyaRTService()
