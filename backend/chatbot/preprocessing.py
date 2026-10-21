import json
from pathlib import Path

dataset_path = Path(__file__).parent / "dataset" / "knowledgebase.jsonl"

# Membaca dataset
def baca_dataset():
    data = []

    with open(dataset_path, "r", encoding="utf-8") as file:
        for baris in file:
            if baris.strip():
                data.append(json.loads(baris))

    return data


# Memilih data referensi
def pilih_referensi(data):
    referensi = []

    for item in data:
        if (item["jenis_sumber"] == "pemerintah"
                and item["kelayakan_rag"] == "REFERENSI_PUBLIK_DENGAN_LABEL_INSTANSI"):
            referensi.append(item)

    return referensi


if __name__ == "__main__":
    data = baca_dataset()
    referensi = pilih_referensi(data)

    print("Total data:", len(data))
    print("Data referensi:", len(referensi))

    for item in referensi[:3]:
        print("-", item["judul"])