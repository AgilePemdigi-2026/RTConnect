"""Harness Pengukuran Latensi TanyaRT (Safe / Non-destructive).

Standar Pengujian:
1. Mode DEFAULT adalah aman (MOCK / LOCAL IN-MEMORY STUB):
   - Tidak menyentuh database live bersama.
   - Tidak memilih warga sembarang atau menandatangani token warga nyata.
   - Menggunakan stub terisolasi dengan data fixture.
2. Mode LIVE (--live):
   - Wajib secara eksplisit menyertakan flag --confirm-live-db dan kredensial/token uji.
   - Jika tidak ada konfirmasi izin eksplisit, skrip menolak berjalan demi keamanan database bersama.
3. Rekaman Bukti:
   - Menghasilkan berkas CSV baru dengan Run ID ber-timestamp unik (tidak menimpa bukti lama).
   - Mencatat metadata lingkungan, status HTTP, durasi (ms), status fungsional, dan penilaian lulus yang jujur
     (target_met: total_ms <= 5000 DAN status HTTP 200 DAN validasi fungsional terpenuhi).
   - Bersih dari token, kredensial, atau isi pesan pribadi.
"""

import argparse
import csv
import datetime
from pathlib import Path
import sys
import time

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import jwt
from config import Config
from services import rag_service as rag

BUKTI_DIR = BACKEND_DIR.parent / "docs" / "audit" / "bukti"
BUKTI_DIR.mkdir(parents=True, exist_ok=True)


def create_mock_app_harness():
    """Bentuk instance test_client terisolasi tanpa akses DB bersama dan tanpa panggilan jaringan luar."""
    from flask import Flask
    import routes.chatbot_routes as chatbot_routes
    import middleware.auth_middleware as auth_mw
    import services.semantic_embedding_service as sem_service
    import services.tanyart_llm_service as llm_service
    from regresi_retrieval_offline import load_chunks
    from contextlib import contextmanager

    chunks = load_chunks()

    app = Flask("tanyart_latency_harness_mock")
    app.register_blueprint(chatbot_routes.chatbot_bp)

    # 1. Isolasi Autentikasi Pengguna Uji (bukan warga sembarang dari DB)
    auth_mw.get_user = lambda role, uid: {
        "user_id": 9999,
        "role": "warga",
        "nama_lengkap": "Warga Uji Terisolasi",
        "email": "warga.uji@example.test",
        "is_active": True,
    }

    # 2. Isolasi Database (In-Memory Stubs, zero DB writes/reads)
    stored_mock_history = ["Jadwal kerja bakti RT dilaksanakan setiap hari Minggu pertama."]
    chatbot_routes.query_one = lambda sql, p=None: {"chat_session_id": 9999, "warga_id": 9999}
    chatbot_routes.query_all = lambda sql, p=None: (
        [{"isi_pesan": h} for h in reversed(stored_mock_history)]
        if "from chatmessage" in sql.lower()
        else chunks
    )
    rag.query_all = lambda sql, p=None: chunks
    chatbot_routes.execute = lambda *a, **k: 1
    chatbot_routes.execute_returning = lambda *a, **k: {"chat_session_id": 9999, "message_id": 9999}
    chatbot_routes.first_rt_id = lambda: 1

    @contextmanager
    def tx():
        class Cur:
            def execute(s, *a, **k): pass
            def fetchone(s): return {"message_id": 9999}
        yield Cur()

    chatbot_routes.transaction = tx

    # 3. Isolasi Total Provider Eksternal (Gemini & OpenAI di-mock / zero network call)
    sem_service.is_embedding_configured = lambda: False
    rag.is_embedding_configured = lambda: False

    def mock_synthesize(query, chunk, conversation_history=None, timeout=None, time_budget=None):
        ans = llm_service.format_fallback_answer(chunk)
        cit = llm_service.build_citation(chunk)
        return f"{ans} (Mock AI Synthesized)", cit, True

    llm_service.synthesize_answer_with_gemini = mock_synthesize
    rag.synthesize_answer_with_gemini = mock_synthesize

    return app.test_client()


def run_latency_measurement(mode="mock", confirm_live=False, test_token=None, test_session_id=None):
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"RUN_{timestamp_str}_{mode.upper()}"
    output_csv = BUKTI_DIR / f"latensi_tanyart_{run_id}.csv"

    print(f"=== TANYART LATENCY HARNESS (Run ID: {run_id}) ===")
    print(f"Mode Pengukuran : {mode.upper()}")

    if mode == "live":
        if not confirm_live:
            print("[DITOLAK] Mode live membutuhkan flag --confirm-live-db untuk melindungi database bersama.")
            sys.exit(1)
        if not test_token:
            print("[DITOLAK] Mode live membutuhkan token uji resmi (--test-token) untuk mencegah pemalsuan identitas warga.")
            sys.exit(1)
        from app import create_app
        client = create_app().test_client()
        auth_token = test_token
        session_id = test_session_id
    else:
        client = create_mock_app_harness()
        auth_token = jwt.encode(
            {"sub": "9999", "role": "warga", "email": "warga.uji@example.test", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
            Config.JWT_SECRET,
            algorithm="HS256",
        )
        session_id = 9999

    test_cases = [
        {"id": "SCN-01", "name": "Cache Kosong / Pasca-Restart (KK Rusak)", "query": "Bagaimana syarat mengganti Kartu Keluarga yang rusak?", "cache": "invalidate", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-02", "name": "Cache Terisi (KK Rusak)", "query": "Bagaimana syarat mengganti Kartu Keluarga yang rusak?", "cache": "warm", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-03", "name": "Cache Terisi (Iuran RT Bulan Ini)", "query": "Iuran RT Bulan Ini", "cache": "warm", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-04", "name": "Cache Terisi (Jadwal Kerja Bakti)", "query": "Jadwal Kerja Bakti", "cache": "warm", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-05", "name": "Cache Terisi (Surat Domisili Usaha)", "query": "Bagaimana membuat surat domisili untuk usaha?", "cache": "warm", "exp_status": "KLARIFIKASI_DIBUTUHKAN"},
        {"id": "SCN-06", "name": "Cache Kedaluwarsa (KTP Hilang)", "query": "Bagaimana mengurus KTP yang hilang di Surabaya?", "cache": "expire", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-07", "name": "Cache Terisi (SKCK Online)", "query": "Bagaimana prosedur pembuatan SKCK secara online?", "cache": "warm", "exp_status": "SUMBER_DITEMUKAN"},
        {"id": "SCN-08", "name": "Cache Terisi (Follow-up Jam Kerja Bakti)", "query": "Mulai jam berapa?", "cache": "warm", "exp_status": "SUMBER_DITEMUKAN"},
    ]

    records = []
    for tc in test_cases:
        if tc["cache"] == "invalidate":
            rag.invalidate_knowledge_chunks_cache()
        elif tc["cache"] == "expire":
            rag._CHUNKS_CACHE_TIME = time.perf_counter() - 120.0

        t0 = time.perf_counter()
        resp_json = None
        resp_status = 500
        try:
            resp = client.post(
                "/api/v1/chatbot/query",
                json={"session_id": session_id, "query": tc["query"]},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            total_ms = (time.perf_counter() - t0) * 1000
            resp_status = resp.status_code
            try:
                resp_json = resp.get_json()
            except Exception:
                resp_json = None
        except Exception as e:
            total_ms = (time.perf_counter() - t0) * 1000
            resp_json = None

        # Tangani HTTP error, JSON tidak valid, dan data=null sebagai hasil FAIL yang tercatat
        is_valid_json = isinstance(resp_json, dict)
        data = resp_json.get("data") if is_valid_json else None
        has_valid_data = isinstance(data, dict)

        status = data.get("status", "ERROR") if has_valid_data else "ERROR"
        mode_ret = data.get("retrieval_mode", "UNKNOWN") if has_valid_data else "UNKNOWN"
        is_esc = data.get("is_escalated", False) if has_valid_data else False
        ai_gen = data.get("ai_generated", False) if has_valid_data else False

        functional_ok = (
            resp_status == 200
            and is_valid_json
            and has_valid_data
            and status == tc["exp_status"]
            and data.get("answer") is not None
        )
        target_met = (total_ms <= 5000.0 and functional_ok)

        rec = {
            "run_id": run_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "scenario_id": tc["id"],
            "scenario_name": tc["name"],
            "cache_state": tc["cache"],
            "http_code": resp_status,
            "total_ms": round(total_ms, 2),
            "status": status,
            "retrieval_mode": mode_ret,
            "is_escalated": is_esc,
            "ai_generated": ai_gen,
            "functional_ok": functional_ok,
            "target_met": target_met,
        }
        records.append(rec)
        print(f"[{rec['scenario_id']}] {rec['scenario_name']:<42} : {rec['total_ms']:7.2f} ms | Status={rec['status']:<22} | Valid={functional_ok} | Lolos={target_met}")

    # Hitung metrik agregat
    total_samples = len(records)
    durations = [r["total_ms"] for r in records]
    avg_ms = sum(durations) / total_samples
    max_ms = max(durations)
    exceed_count = sum(1 for d in durations if d > 5000.0)
    passed_count = sum(1 for r in records if r["target_met"])

    print("-" * 75)
    print(f"Total Sampel : {total_samples}")
    print(f"Rata-rata    : {avg_ms:.2f} ms")
    print(f"Maksimum     : {max_ms:.2f} ms")
    print(f"Melewati 5s  : {exceed_count} sampel")
    print(f"Total Lolos  : {passed_count}/{total_samples}")

    # Simpan CSV unik tanpa menimpa bukti lama
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"[BUKTI TERSIMPAN] {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harness Pengukuran Latensi TanyaRT")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Mode pengukuran (default: mock)")
    parser.add_argument("--confirm-live-db", action="store_true", help="Konfirmasi otorisasi akses database live")
    parser.add_argument("--test-token", type=str, default=None, help="JWT token akun uji untuk mode live")
    parser.add_argument("--test-session-id", type=int, default=None, help="ID sesi uji untuk mode live")
    args = parser.parse_args()

    run_latency_measurement(
        mode=args.mode,
        confirm_live=args.confirm_live_db,
        test_token=args.test_token,
        test_session_id=args.test_session_id,
    )
