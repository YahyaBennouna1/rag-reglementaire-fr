"""BM25 sous forme de vecteurs creux dans Qdrant.

Formule BM25 pour un terme t d'un passage d :
    score(t, d) = IDF(t) × tf × (k1 + 1) / (tf + k1 × (1 - b + b × longueur(d) / longueur_moyenne))

- La partie de droite (fréquence du terme, « saturée ») est calculée ici, à l'indexation.
- L'IDF (rareté du terme dans le corpus) est calculée par Qdrant (option modifier=IDF).
La question est un vecteur creux avec un poids 1 par terme : le produit des deux donne BM25.
"""

import zlib
from collections import Counter

from qdrant_client import QdrantClient, models

from ragfr.models import Passage
from ragfr.retrieval.french_analyzer import analyze

K1 = 1.2  # vitesse de saturation : la 10e répétition d'un mot compte bien moins que la 1re
B = 0.75  # force de la normalisation par la longueur du passage


def term_id(term: str) -> int:
    """Chaque terme devient un numéro stable (le même à chaque lancement)."""
    return zlib.crc32(term.encode())


def document_vector(text: str, avg_len: float) -> models.SparseVector:
    terms = analyze(text)
    counts = Counter(terms)
    length = len(terms)
    weights: dict[int, float] = {}
    for term, tf in counts.items():
        weight = tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / avg_len))
        weights[term_id(term)] = weights.get(term_id(term), 0.0) + weight
    return models.SparseVector(indices=list(weights), values=list(weights.values()))


def query_vector(text: str) -> models.SparseVector:
    ids = sorted({term_id(t) for t in analyze(text)})
    return models.SparseVector(indices=ids, values=[1.0] * len(ids))


def average_length(texts: list[str]) -> float:
    return sum(len(analyze(t)) for t in texts) / max(len(texts), 1)


class BM25Retriever:
    def __init__(self, client: QdrantClient, collection: str):
        self.client = client
        self.collection = collection

    def search(self, query: str, k: int, dense_query: str | None = None) -> list[Passage]:
        # BM25 cherche toujours avec la vraie question : `dense_query` est ignoré.
        vector = query_vector(query)
        if not vector.indices:  # question faite uniquement de mots vides
            return []
        hits = self.client.query_points(
            self.collection, query=vector, using="bm25", limit=k, with_payload=True
        )
        return [Passage(**hit.payload, score=hit.score) for hit in hits.points]
