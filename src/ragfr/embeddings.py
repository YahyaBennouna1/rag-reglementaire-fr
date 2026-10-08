"""Embeddings denses avec bge-m3, et un cache SQLite pour ne jamais recalculer un même texte.

Encoder tout le corpus prend plusieurs dizaines de minutes sur CPU. Comme les méthodes
de chunking produisent souvent les mêmes textes, le cache évite de les ré-encoder.
"""

import hashlib
import sqlite3
from functools import cached_property
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE_DB = ROOT / "data" / "cache" / "embeddings.sqlite"


class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", batch_size: int = 8):
        self.model_name = model_name
        self.batch_size = batch_size
        CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(CACHE_DB)
        self.db.execute("CREATE TABLE IF NOT EXISTS emb (key TEXT PRIMARY KEY, vec BLOB)")

    @cached_property
    def model(self):
        # Import et chargement seulement au premier besoin : ~2 Go en mémoire.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name, device="cpu")

    @property
    def dim(self) -> int:
        return 1024  # taille des vecteurs de bge-m3

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model_name}\n{text}".encode()).hexdigest()

    def encode(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        """Renvoie une matrice (len(texts), dim) de vecteurs normalisés (norme 1)."""
        keys = [self._key(t) for t in texts]
        found = {}
        for i in range(0, len(keys), 500):  # SQLite limite le nombre de paramètres par requête
            chunk = keys[i : i + 500]
            marks = ",".join("?" * len(chunk))
            for key, blob in self.db.execute(f"SELECT key, vec FROM emb WHERE key IN ({marks})", chunk):
                found[key] = np.frombuffer(blob, dtype=np.float32)

        missing = [i for i, k in enumerate(keys) if k not in found]
        if missing:
            vectors = self.model.encode(
                [texts[i] for i in missing],
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=show_progress,
            ).astype(np.float32)
            rows = [(keys[i], vec.tobytes()) for i, vec in zip(missing, vectors, strict=True)]
            self.db.executemany("INSERT OR REPLACE INTO emb VALUES (?, ?)", rows)
            self.db.commit()
            for i, vec in zip(missing, vectors, strict=True):
                found[keys[i]] = vec

        return np.stack([found[k] for k in keys]) if keys else np.zeros((0, self.dim), dtype=np.float32)
