"""Recherche dense : la question et les passages sont des vecteurs, on cherche les plus proches."""

from qdrant_client import QdrantClient

from ragfr.embeddings import Embedder
from ragfr.models import Passage


class DenseRetriever:
    def __init__(self, client: QdrantClient, collection: str, embedder: Embedder):
        self.client = client
        self.collection = collection
        self.embedder = embedder

    def search(self, query: str, k: int) -> list[Passage]:
        vector = self.embedder.encode([query])[0]
        hits = self.client.query_points(
            self.collection, query=vector.tolist(), using="dense", limit=k, with_payload=True
        )
        return [Passage(**hit.payload, score=hit.score) for hit in hits.points]
