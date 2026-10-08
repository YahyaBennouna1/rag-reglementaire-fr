"""Recherche hybride : BM25 + dense, fusionnés par RRF."""

from ragfr.models import Passage
from ragfr.retrieval.bm25 import BM25Retriever
from ragfr.retrieval.dense import DenseRetriever
from ragfr.retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    def __init__(
        self,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        candidates: int = 50,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
    ):
        self.bm25 = bm25
        self.dense = dense
        self.candidates = candidates  # nombre de résultats demandés à chaque moteur avant la fusion
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight

    def search(self, query: str, k: int, dense_query: str | None = None) -> list[Passage]:
        lexical = self.bm25.search(query, self.candidates)
        semantic = self.dense.search(query, self.candidates, dense_query=dense_query)
        fused = reciprocal_rank_fusion([lexical, semantic], k=self.rrf_k, weights=[self.bm25_weight, 1.0])
        return fused[:k]
