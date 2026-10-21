import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from preprocessing import baca_dataset, pilih_referensi

data = baca_dataset()
referensi = pilih_referensi(data)
teks = [
    f"{item['judul']}. {item['konten']}"
    for item in referensi
]

#embedding model
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

embeddings = model.encode(
    teks,
    normalize_embeddings=True,
    show_progress_bar=True
)

folder_output = Path(__file__).parent / "cache"
folder_output.mkdir(exist_ok=True)

# hasil
np.save(folder_output / "embeddings.npy", embeddings)

# ID dokumen
ids = [item["id"] for item in referensi]

with open(folder_output / "ids.json", "w", encoding="utf-8") as file:
    json.dump(ids, file, indent=2)

print("Jumlah dokumen:", len(teks))
print("Ukuran embedding:", embeddings.shape)
print("Embedding berhasil disimpan")
