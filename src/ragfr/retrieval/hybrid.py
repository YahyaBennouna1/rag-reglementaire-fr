"""Recherche hybride : BM25 + dense, fusionnés par RRF."""

from ragfr.models import Passage
from ragfr.retrieval.bm25 import BM25Retriever
from ragfr.retrieval.dense import DenseRetriever
from ragfr.retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    def __init__(self, bm25: BM25Retriever, dense: DenseRetriever, candidates: int = 50, rrf_k: int = 60):
        self.bm25 = bm25
        self.dense = dense
        self.candidates = candidates  # nombre de résultats demandés à chaque moteur avant la fusion
        self.rrf_k = rrf_k

    def search(self, query: str, k: int, dense_query: str | None = None) -> list[Passage]:
        lexical = self.bm25.search(query, self.candidates)
        semantic = self.dense.search(query, self.candidates, dense_query=dense_query)
        return reciprocal_rank_fusion([lexical, semantic], k=self.rrf_k)[:k]
