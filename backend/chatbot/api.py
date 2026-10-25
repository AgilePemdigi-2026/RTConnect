
import os
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, Field

from .chatbot_service import get_service


app = FastAPI(
    title="TanyaRT Internal API",
    docs_url=None,
    redoc_url=None
)

security = HTTPBearer(auto_error=False)


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
        max_length=1000
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

    result = get_service().jawab(
        payload.question,
        rt_id=payload.rt_id,
        dokumen_lokal=[
            dok.model_dump()
            for dok in payload.local_documents
        ]
    )

    return {
        "success": True,
        "data": result,
        "error": None
    }
