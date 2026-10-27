
import json
from pathlib import Path

DATASET = Path(__file__).parent / "dataset" / "knowledgebase.jsonl"


def baca_dataset():
    with DATASET.open(encoding="utf-8") as file:
        return [
            json.loads(baris)
            for baris in file
            if baris.strip()
        ]


def pilih_referensi(data):
    return [
        item for item in data
        if item.get("jenis_sumber") == "pemerintah"
        and item.get("kelayakan_rag")
        == "REFERENSI_PUBLIK_DENGAN_LABEL_INSTANSI"
        and item.get("id")
        and item.get("judul")
        and item.get("konten")
        and item.get("url_sumber")
    ]


if __name__ == "__main__":
    data = baca_dataset()
    referensi = pilih_referensi(data)

    print("Total dataset:", len(data))
    print("Referensi pemerintah:", len(referensi))