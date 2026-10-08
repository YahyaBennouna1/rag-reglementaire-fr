"""Reranker « cross-encoder » : relit chaque passage AVEC la question pour mieux les classer.

Un embedding encode la question et le passage séparément (rapide, mais approximatif).
Un cross-encoder lit les deux ensemble : il voit si le passage répond vraiment à la question.
Beaucoup plus précis, mais beaucoup plus lent : on ne l'applique qu'aux 30 meilleurs candidats.
"""

import hashlib
import sqlite3
from functools import cached_property
from pathlib import Path

from ragfr.models import Passage

ROOT = Path(__file__).resolve().parents[3]
CACHE_DB = ROOT / "data" / "cache" / "rerank.sqlite"


class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", batch_size: int = 8):
        self.model_name = model_name
        self.batch_size = batch_size
        CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(CACHE_DB)
        self.db.execute("CREATE TABLE IF NOT EXISTS scores (key TEXT PRIMARY KEY, score REAL)")

    @cached_property
    def model(self):
        from sentence_transformers import CrossEncoder

        return CrossEncoder(self.model_name, device="cpu", max_length=1024)

    def _key(self, query: str, text: str) -> str:
        return hashlib.sha256(f"{self.model_name}\n{query}\n{text}".encode()).hexdigest()

    def rerank(self, query: str, passages: list[Passage], top_n: int) -> list[Passage]:
        keys = [self._key(query, p.index_text) for p in passages]
        scores = {}
        for key in keys:
            row = self.db.execute("SELECT score FROM scores WHERE key = ?", (key,)).fetchone()
            if row:
                scores[key] = row[0]

        missing = [i for i, key in enumerate(keys) if key not in scores]
        if missing:
            pairs = [(query, passages[i].index_text) for i in missing]
            new_scores = self.model.predict(pairs, batch_size=self.batch_size)
            for i, score in zip(missing, new_scores, strict=True):
                scores[keys[i]] = float(score)
                self.db.execute("INSERT OR REPLACE INTO scores VALUES (?, ?)", (keys[i], float(score)))
            self.db.commit()

        rescored = [
            p.model_copy(update={"score": scores[key]}) for p, key in zip(passages, keys, strict=True)
        ]
        rescored.sort(key=lambda p: p.score, reverse=True)
        return rescored[:top_n]


class RerankingRetriever:
    """Enveloppe n'importe quel moteur de recherche : il fournit les candidats, le reranker les reclasse."""

    def __init__(self, base, reranker: Reranker, candidates: int = 30):
        self.base = base
        self.reranker = reranker
        self.candidates = candidates

    def search(self, query: str, k: int) -> list[Passage]:
        return self.reranker.rerank(query, self.base.search(query, self.candidates), top_n=k)
