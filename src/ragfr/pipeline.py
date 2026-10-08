"""Assemble les briques décrites dans la config (le YAML décide, le code exécute)."""

from functools import cache

from ragfr.config import Config
from ragfr.embeddings import Embedder
from ragfr.index import collection_name, get_client
from ragfr.retrieval.base import Retriever
from ragfr.retrieval.bm25 import BM25Retriever
from ragfr.retrieval.dense import DenseRetriever
from ragfr.retrieval.hybrid import HybridRetriever
from ragfr.retrieval.reranker import Reranker, RerankingRetriever


@cache
def get_embedder() -> Embedder:
    return Embedder()


@cache
def get_reranker() -> Reranker:
    return Reranker()


def make_retriever(cfg: Config) -> Retriever:
    client, collection = get_client(), collection_name(cfg.chunking)
    r = cfg.retrieval

    if r.mode == "dense":
        retriever = DenseRetriever(client, collection, get_embedder())
    elif r.mode == "bm25":
        retriever = BM25Retriever(client, collection)
    else:
        retriever = HybridRetriever(
            BM25Retriever(client, collection),
            DenseRetriever(client, collection, get_embedder()),
            candidates=r.candidates,
            rrf_k=r.rrf_k,
        )

    if r.reranker:
        retriever = RerankingRetriever(retriever, get_reranker(), candidates=r.rerank_candidates)
    return retriever
