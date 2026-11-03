import hashlib
import os
from datetime import date
from functools import lru_cache

try:
    try:
        from .retrieval import HybridRetriever
        from .rules import (
            jenis_pertanyaan,
            semua_topik,
            aksi_pertanyaan,
            coverage,
            penentu_hilang,
        )
    except (ImportError, ModuleNotFoundError):
        from retrieval import HybridRetriever
        from rules import (
            jenis_pertanyaan,
            semua_topik,
            aksi_pertanyaan,
            coverage,
            penentu_hilang,
        )
except Exception:
    HybridRetriever = None
    jenis_pertanyaan = semua_topik = aksi_pertanyaan = coverage = penentu_hilang = None


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

# Ambang bawaan. SEMUANYA SEMENTARA: kalibrasi dari hasil evaluation.py
# lalu atur lewat variabel lingkungan.
MIN_SKOR = 0.70              # cukup kuat (bersama topik & aksi cocok)
MIN_SKOR_KONSENSUS = 0.50    # boleh jika semantic dan BM25 sepakat
MIN_SKOR_LOKAL = 0.40        # dokumen SOP RT
MIN_COVERAGE_LOKAL = 0.67    # porsi kata penting yang ada di SOP RT


def _env_float(nama, bawaan):
    nilai = float(os.getenv(nama, str(bawaan)))

    if not 0 <= nilai <= 1:
        raise ValueError(f"{nama} harus antara 0 dan 1")

    return nilai


def hasil(status, jawaban, sumber=None, skor=None, alasan=None):

    sumber = sumber or []

    return {
        "status": status,
        "reason": alasan,
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


def potong_kalimat(teks, batas=600):
    """Potong di batas kalimat/kata, bukan di tengah kata."""
    teks = " ".join(str(teks).split())

    if len(teks) <= batas:
        return teks

    potong = teks[:batas]
    akhir = potong.rfind(". ")

    if akhir >= batas // 3:
        return potong[:akhir + 1]

    return potong.rsplit(" ", 1)[0] + "…"


def catatan_wilayah(item):
    wilayah = (item.get("wilayah") or "").strip()

    if wilayah and wilayah.lower() != "nasional":
        return f" (Informasi ini berlaku untuk wilayah {wilayah}.)"

    return ""


def _id_unik(item):
    isi = f"{item['id']}|{item['judul']}|{item['konten']}"
    return hashlib.sha256(isi.encode("utf-8")).hexdigest()


class TanyaRTService:

    def __init__(self):
        if HybridRetriever is None:
            raise RuntimeError("Pustaka retrieval (numpy/sentence-transformers) belum terpasang.")
        self.retriever = HybridRetriever()

        self.min_skor = _env_float(
            "CHATBOT_MIN_SCORE", MIN_SKOR
        )
        self.min_konsensus = _env_float(
            "CHATBOT_MIN_SCORE_KONSENSUS", MIN_SKOR_KONSENSUS
        )
        self.min_lokal = _env_float(
            "CHATBOT_MIN_SCORE_LOKAL", MIN_SKOR_LOKAL
        )
        self.min_coverage_lokal = _env_float(
            "CHATBOT_MIN_COVERAGE_LOKAL", MIN_COVERAGE_LOKAL
        )

        if self.min_konsensus > self.min_skor:
            raise ValueError(
                "CHATBOT_MIN_SCORE_KONSENSUS tidak boleh "
                "lebih besar dari CHATBOT_MIN_SCORE"
            )

        # Cache embedding dokumen SOP RT: {hash isi: vektor}
        self._cache_lokal = {}

    # ---------------- SOP RT ----------------

    def _vektor_lokal(self, dokumen):
        kunci = [_id_unik(d) for d in dokumen]
        belum = [
            (k, d) for k, d in zip(kunci, dokumen)
            if k not in self._cache_lokal
        ]

        if belum:
            vektor = self.retriever.model.encode(
                [d["judul"] + ". " + d["konten"] for _, d in belum],
                normalize_embeddings=True
            )

            for (k, _), v in zip(belum, vektor):
                self._cache_lokal[k] = v

        return [self._cache_lokal[k] for k in kunci]

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
                PESAN["BELUM_ADA_SOP_RT"],
                alasan="RT_TIDAK_DIKETAHUI"
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
                PESAN["BELUM_ADA_SOP_RT"],
                alasan="TIDAK_ADA_DOKUMEN_RT"
            )

        vektor_dokumen = self._vektor_lokal(kandidat)

        vektor_tanya = self.retriever.model.encode(
            [pertanyaan],
            normalize_embeddings=True
        )[0]

        skor = [float(v @ vektor_tanya) for v in vektor_dokumen]
        indeks = max(range(len(skor)), key=lambda i: skor[i])
        dokumen = kandidat[indeks]

        cakupan = coverage(
            pertanyaan,
            dokumen["judul"] + " " + dokumen["konten"]
        )

        if (
            skor[indeks] < self.min_lokal
            or cakupan < self.min_coverage_lokal
            or penentu_hilang(pertanyaan, dokumen["konten"])
        ):
            return hasil(
                "BELUM_ADA_SOP_RT",
                PESAN["BELUM_ADA_SOP_RT"],
                alasan="SOP_RT_TIDAK_MENJAWAB"
            )

        kutipan = potong_kalimat(dokumen["konten"])

        return hasil(
            "SUMBER_DITEMUKAN",
            (
                "Menurut SOP RT terverifikasi "
                f"'{dokumen['judul']}': {kutipan}"
            ),
            [sumber_dokumen(dokumen)],
            skor[indeks],
            alasan="SOP_RT_COCOK"
        )

    # ---------------- Referensi pemerintah ----------------

    def jawab_pemerintah(self, pertanyaan):

        topik = semua_topik(pertanyaan)
        aksi = aksi_pertanyaan(pertanyaan)

        calon = self.retriever.cari(pertanyaan, top_k=5)

        kandidat = [
            item for item in calon
            if item["topik"] in topik
        ][:3]

        if not kandidat:
            return hasil(
                "PERLU_VERIFIKASI",
                PESAN["PERLU_VERIFIKASI"],
                alasan="TOPIK_TIDAK_COCOK"
            )

        sumber = [sumber_dokumen(item) for item in kandidat]
        terbaik = kandidat[0]
        skor = terbaik["skor_semantik"]

        def tidak_pasti(alasan):
            return hasil(
                "PERLU_VERIFIKASI",
                PESAN["PERLU_VERIFIKASI"]
                + f" Sumber terkait: {terbaik['judul']}"
                + (
                    f" ({sumber[0]['url']})"
                    if sumber[0]["url"] else ""
                ),
                sumber,
                skor,
                alasan=alasan
            )

        # Pertanyaan menyangkut lebih dari satu topik
        if len(topik) > 1:
            return tidak_pasti("BANYAK_TOPIK")

        # Aksi pada pertanyaan berbeda dengan aksi dokumen
        if (
            aksi is not None
            and terbaik["aksi"] is not None
            and aksi != terbaik["aksi"]
        ):
            return tidak_pasti("AKSI_TIDAK_COCOK")

        # Menanyakan biaya/denda tetapi dokumen tidak membahasnya
        if penentu_hilang(
            pertanyaan,
            terbaik["judul"] + " " + terbaik["konten"]
        ):
            return tidak_pasti("KATA_PENENTU_TIDAK_ADA")

        konsensus = (
            terbaik["rank_semantik"] <= 2
            and terbaik["rank_bm25"] <= 2
        )

        if skor >= self.min_skor:
            alasan = "SKOR_TINGGI"

        elif (
            skor >= self.min_konsensus
            and konsensus
            and aksi == terbaik["aksi"]
        ):
            alasan = "KONSENSUS"

        else:
            return tidak_pasti("SKOR_RENDAH")

        kutipan = potong_kalimat(terbaik["konten"])

        return hasil(
            "SUMBER_DITEMUKAN",
            (
                f"Menurut sumber resmi '{terbaik['judul']}': "
                f"{kutipan}{catatan_wilayah(terbaik)}"
            ),
            sumber,
            skor,
            alasan=alasan
        )

    # ---------------- Pintu masuk ----------------

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
                "Pertanyaan tidak boleh kosong.",
                alasan="KOSONG"
            )

        jenis = jenis_pertanyaan(pertanyaan)

        if jenis == "RAHASIA":
            return hasil(
                "RAHASIA",
                PESAN["RAHASIA"],
                alasan="MINTA_RAHASIA"
            )

        if jenis == "LUAR_CAKUPAN":
            return hasil(
                "LUAR_CAKUPAN",
                PESAN["LUAR_CAKUPAN"],
                alasan="BUKAN_ADMINISTRASI"
            )

        if jenis == "ADMIN_LAIN":
            return hasil(
                "FALLBACK",
                PESAN["FALLBACK"],
                alasan="ADMINISTRASI_BELUM_ADA_DI_KB"
            )

        if jenis == "LOKAL_RT":
            return self.jawab_lokal(
                pertanyaan,
                rt_id,
                dokumen_lokal or []
            )

        return self.jawab_pemerintah(pertanyaan)


@lru_cache(maxsize=1)
def get_service():
    return TanyaRTService()


# ==========================================
# Cache Integrity & Synchronization Helpers
# ==========================================
from pathlib import Path
import json
import logging

_logger = logging.getLogger(__name__)

CHATBOT_DIR = Path(__file__).parent
DATASET_PATH = CHATBOT_DIR / "dataset" / "knowledgebase.jsonl"
CACHE_DIR = CHATBOT_DIR / "cache"
CACHE_EMBEDDINGS_PATH = CACHE_DIR / "embeddings.npy"
CACHE_IDS_PATH = CACHE_DIR / "ids.json"


def hitung_hash_file(filepath: Path):
    """Menghitung SHA-256 hexdigest dari file target."""
    if not filepath.exists():
        return None
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validasi_integritas_cache():
    """
    Memvalidasi apakah cache embeddings.npy dan ids.json selaras
    dengan isi dokumen referensi di dataset knowledgebase.jsonl.
    """
    if not DATASET_PATH.exists():
        return False, f"File dataset tidak ditemukan: {DATASET_PATH}"
    if not CACHE_EMBEDDINGS_PATH.exists():
        return False, f"File cache embedding tidak ditemukan: {CACHE_EMBEDDINGS_PATH}"
    if not CACHE_IDS_PATH.exists():
        return False, f"File cache ID tidak ditemukan: {CACHE_IDS_PATH}"

    try:
        from .preprocessing import baca_dataset, pilih_referensi
    except ImportError:
        try:
            from preprocessing import baca_dataset, pilih_referensi
        except ImportError:
            import sys
            sys.path.insert(0, str(CHATBOT_DIR))
            from preprocessing import baca_dataset, pilih_referensi

    try:
        data = baca_dataset()
        referensi = pilih_referensi(data)
        dataset_ids = [item["id"] for item in referensi]
    except Exception as e:
        return False, f"Gagal membaca dataset knowledgebase: {e}"

    try:
        with open(CACHE_IDS_PATH, "r", encoding="utf-8") as f:
            cached_ids = json.load(f)
    except Exception as e:
        return False, f"Gagal membaca cache ids.json: {e}"

    if cached_ids != dataset_ids:
        return False, f"Cache ID ({len(cached_ids)}) tidak cocok dengan ID referensi dataset ({len(dataset_ids)})."

    return True, "Cache embedding dan dataset referensi tersinkronisasi sempurna."
