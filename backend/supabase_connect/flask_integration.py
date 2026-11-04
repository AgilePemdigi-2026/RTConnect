"""Menempelkan Supabase ke Flask.

Di backend/app.py, dalam create_app():
    from supabase_connect.flask_integration import init_supabase
    init_supabase(app)
"""

from __future__ import annotations

import os

from flask import Blueprint, Flask, jsonify

from .config import get_settings
from .errors import SupabaseConfigError
from .health import check_connection

supabase_bp = Blueprint("supabase_connect", __name__, url_prefix="/api/v1/supabase")


@supabase_bp.route("/health", methods=["GET"])
def supabase_health():
    try:
        get_settings()
    except SupabaseConfigError:
        return jsonify({
            "success": False,
            "message": "Supabase belum dikonfigurasi",
            "data": None,
            "error": "SUPABASE_NOT_CONFIGURED",
        }), 503

    result = check_connection()
    ok = result["ok"]
    return jsonify({
        "success": ok,
        "message": "Koneksi Supabase berfungsi" if ok else "Koneksi Supabase bermasalah",
        "data": {"status": "ok" if ok else "unavailable", "latency_ms": result["latency_ms"]},
        "error": None if ok else "SUPABASE_UNAVAILABLE",
    }), 200 if ok else 503


def init_supabase(app: Flask) -> None:
    app.register_blueprint(supabase_bp)

    if os.getenv("SUPABASE_FAIL_FAST", "false").lower() in {"1", "true", "yes"}:
        get_settings()
        result = check_connection()
        if not result["ok"]:
            raise RuntimeError(f"Supabase tidak dapat dihubungi saat startup: {result['error']}")
    else:
        try:
            result = check_connection()
            if not result["ok"]:
                app.logger.warning("Supabase belum bisa dihubungi: %s", result["error"])
        except SupabaseConfigError as exc:
            app.logger.warning("Supabase dilewati: %s", exc)