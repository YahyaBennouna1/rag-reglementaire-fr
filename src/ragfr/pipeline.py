"""Assemble les briques décrites dans la config (le YAML décide, le code exécute)."""

from functools import cache

from ragfr.config import Config
from ragfr.embeddings import Embedder
from ragfr.index import collection_name, get_client
from ragfr.retrieval.base import Retriever
from ragfr.retrieval.dense import DenseRetriever


@cache
def get_embedder() -> Embedder:
    return Embedder()


def make_retriever(cfg: Config) -> Retriever:
    if cfg.retrieval.mode == "dense":
        return DenseRetriever(get_client(), collection_name(cfg.chunking), get_embedder())
    raise NotImplementedError(f"mode de recherche pas encore implémenté : {cfg.retrieval.mode}")
