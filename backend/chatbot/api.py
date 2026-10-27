import logging
import os
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .chatbot_service import get_service


logger = logging.getLogger("tanyart")


@asynccontextmanager
async def lifespan(app):
    # Muat model & cache saat startup. Jika cache tidak cocok,
    # server gagal start (lebih baik daripada gagal di request pertama).
    get_service()
    logger.info("TanyaRT siap")
    yield


app = FastAPI(
    title="TanyaRT Internal API",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

security = HTTPBearer(auto_error=False)


def galat(kode, pesan):
    return JSONResponse(
        status_code=kode,
        content={
            "success": False,
            "data": None,
            "error": {"code": kode, "message": pesan}
        }
    )


@app.exception_handler(StarletteHTTPException)
async def tangani_http(request: Request, exc):
    return galat(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def tangani_validasi(request: Request, exc):
    return galat(422, "Format permintaan tidak valid")


@app.exception_handler(Exception)
async def tangani_umum(request: Request, exc):
    # Jangan bocorkan detail internal ke klien
    logger.exception("Kesalahan tak terduga")
    return galat(500, "Terjadi kesalahan pada layanan chatbot")


class DokumenRT(BaseModel):
    id: str | int
    rt_id: str | int
    judul: str = Field(
        min_length=1,
        max_length=200
    )
    konten: str = Field(
        min_length=1,
        max_length=10000
    )
    status_verifikasi: str
    url_sumber: str | None = None
    berlaku_sampai: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000
    )

    rt_id: str | int | None = None

    local_documents: list[DokumenRT] = Field(
        default_factory=list,
        max_length=30
    )


def autentikasi(
    credentials: HTTPAuthorizationCredentials | None
    = Depends(security)
):

    token = os.getenv(
        "CHATBOT_INTERNAL_TOKEN",
        ""
    )

    if not token:
        raise HTTPException(
            503,
            "CHATBOT_INTERNAL_TOKEN belum dikonfigurasi"
        )

    if (
        credentials is None
        or not secrets.compare_digest(
            credentials.credentials,
            token
        )
    ):
        raise HTTPException(
            401,
            "Unauthorized"
        )


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/internal/chatbot/query",
    dependencies=[Depends(autentikasi)]
)
def query(payload: ChatRequest):

    mulai = time.perf_counter()

    result = get_service().jawab(
        payload.question,
        rt_id=payload.rt_id,
        dokumen_lokal=[
            dok.model_dump()
            for dok in payload.local_documents
        ]
    )

    # Isi pertanyaan sengaja TIDAK dicatat (bisa berisi data pribadi)
    logger.info(
        "status=%s reason=%s panjang=%d ms=%.0f",
        result["status"],
        result["reason"],
        len(payload.question),
        (time.perf_counter() - mulai) * 1000
    )

    return {
        "success": True,
        "data": result,
        "error": None
    }