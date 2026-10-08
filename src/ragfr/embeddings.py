"""Embeddings denses, avec un cache SQLite pour ne jamais recalculer un même texte.

Le modèle se choisit dans la config (retrieval.embedding_model). Sur un PC à 8 Go de RAM,
bge-m3 (2,2 Go) ne tient pas en mémoire avec le reste du système : la baseline utilise
multilingual-e5-base (1,1 Go). bge-m3 reste disponible, par exemple sur un GPU.
"""

import hashlib
import sqlite3
from functools import cached_property
from pathlib import Path
from typing import Literal

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE_DB = ROOT / "data" / "cache" / "embeddings.sqlite"

# Certains modèles demandent un préfixe différent pour les questions et les passages.
# Sans lui, les e5 marchent beaucoup moins bien (voir leur fiche sur Hugging Face).
PREFIXES = {
    "intfloat/multilingual-e5-small": ("query: ", "passage: "),
    "intfloat/multilingual-e5-base": ("query: ", "passage: "),
    "intfloat/multilingual-e5-large": ("query: ", "passage: "),
}
DIMS = {
    "BAAI/bge-m3": 1024,
    "intfloat/multilingual-e5-small": 384,
    "intfloat/multilingual-e5-base": 768,
    "intfloat/multilingual-e5-large": 1024,
}
SAVE_EVERY = 64  # on écrit dans le cache par paquets : un arrêt en cours de route ne perd presque rien


class Embedder:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-base", batch_size: int = 8):
        self.model_name = model_name
        self.batch_size = batch_size
        CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(CACHE_DB)
        self.db.execute("CREATE TABLE IF NOT EXISTS emb (key TEXT PRIMARY KEY, vec BLOB)")

    @cached_property
    def model(self):
        # Import et chargement seulement au premier besoin : le modèle pèse plus d'1 Go en mémoire.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name, device="cpu")

    @property
    def dim(self) -> int:
        return DIMS.get(self.model_name) or self.model.get_sentence_embedding_dimension()

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model_name}\n{text}".encode()).hexdigest()

    def encode(
        self, texts: list[str], kind: Literal["query", "passage"] = "passage", show_progress: bool = False
    ) -> np.ndarray:
        """Renvoie une matrice (len(texts), dim) de vecteurs normalisés (norme 1)."""
        query_prefix, passage_prefix = PREFIXES.get(self.model_name, ("", ""))
        prefix = query_prefix if kind == "query" else passage_prefix
        texts = [prefix + t for t in texts]
        keys = [self._key(t) for t in texts]

        found = {}
        for i in range(0, len(keys), 500):  # SQLite limite le nombre de paramètres par requête
            chunk = keys[i : i + 500]
            marks = ",".join("?" * len(chunk))
            for key, blob in self.db.execute(f"SELECT key, vec FROM emb WHERE key IN ({marks})", chunk):
                found[key] = np.frombuffer(blob, dtype=np.float32)

        missing = [i for i, k in enumerate(keys) if k not in found]
        for start in range(0, len(missing), SAVE_EVERY):
            batch = missing[start : start + SAVE_EVERY]
            vectors = self.model.encode(
                [texts[i] for i in batch],
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).astype(np.float32)
            rows = [(keys[i], vec.tobytes()) for i, vec in zip(batch, vectors, strict=True)]
            self.db.executemany("INSERT OR REPLACE INTO emb VALUES (?, ?)", rows)
            self.db.commit()
            for i, vec in zip(batch, vectors, strict=True):
                found[keys[i]] = vec
            if show_progress:
                print(f"  embeddings : {min(start + SAVE_EVERY, len(missing))}/{len(missing)}", flush=True)

        return np.stack([found[k] for k in keys]) if keys else np.zeros((0, self.dim), dtype=np.float32)
