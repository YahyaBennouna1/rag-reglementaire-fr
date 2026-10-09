"""Construction de l'index : chunking du corpus, embeddings, chargement dans Qdrant.

Une collection Qdrant par méthode de chunking (ex. "fixed-512-64"), pour comparer les méthodes
sans qu'elles s'écrasent. Qdrant tourne ici en mode local (un dossier), sans serveur.
"""

import os
from functools import cache
from pathlib import Path

from qdrant_client import QdrantClient, models

from ragfr.config import ChunkingConfig, Config
from ragfr.embeddings import Embedder
from ragfr.ingestion.models import ParsedDocument
from ragfr.models import Passage
from ragfr.retrieval.bm25 import average_length, document_vector

ROOT = Path(__file__).resolve().parents[2]
PARSED_DIR = ROOT / "data" / "parsed"
QDRANT_DIR = ROOT / "data" / "qdrant"


def collection_name(cfg: Config) -> str:
    """Une collection par (découpage, modèle d'embedding) : deux modèles n'ont pas les mêmes vecteurs."""
    c = cfg.chunking
    model = cfg.retrieval.embedding_model.split("/")[-1]
    return f"{c.method}-{c.size}-{c.overlap}-{model}"


def load_parsed_documents() -> list[ParsedDocument]:
    paths = sorted(p for p in PARSED_DIR.glob("*.json") if not p.name.endswith(".docling.json"))
    return [ParsedDocument.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def chunk_corpus(chunking: ChunkingConfig) -> list[Passage]:
    # Import ici et pas en haut du fichier : le découpage charge `transformers` (30 s d'import),
    # inutile pour répondre aux questions (API, interface), qui importent aussi ce module.
    from ragfr.chunking.fixed import chunk_fixed

    if chunking.method != "fixed":
        raise NotImplementedError(f"méthode de chunking pas encore implémentée : {chunking.method}")
    passages = []
    for doc in load_parsed_documents():
        passages.extend(chunk_fixed(doc, chunking.size, chunking.overlap))
    return passages


@cache
def get_client() -> QdrantClient:
    """Le client Qdrant du programme, ouvert une seule fois.

    - Si QDRANT_URL est définie (ex. http://qdrant:6333 dans Docker Compose) : Qdrant serveur,
      que plusieurs programmes peuvent utiliser en même temps.
    - Sinon : mode local, un dossier sur le disque. Qdrant le verrouille : un seul programme à la
      fois, et un 2e client dans le même programme lèverait une erreur. D'où le @cache.
    """
    url = os.environ.get("QDRANT_URL")
    if url:
        return QdrantClient(url=url)
    return QdrantClient(path=str(QDRANT_DIR))


def build_index(client: QdrantClient, name: str, passages: list[Passage], embedder: Embedder) -> None:
    """Une collection, deux vecteurs par passage : « dense » (sens) et « bm25 » (mots exacts)."""
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        name,
        vectors_config={"dense": models.VectorParams(size=embedder.dim, distance=models.Distance.COSINE)},
        # modifier=IDF : Qdrant calcule lui-même la rareté de chaque terme dans la collection.
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    texts = [p.index_text for p in passages]
    dense_vectors = embedder.encode(texts, show_progress=True)
    avg_len = average_length(texts)
    client.upload_points(
        name,
        points=[
            models.PointStruct(
                id=i,
                vector={"dense": vec.tolist(), "bm25": document_vector(text, avg_len)},
                payload=p.model_dump(exclude={"score"}),
            )
            for i, (p, text, vec) in enumerate(zip(passages, texts, dense_vectors, strict=True))
        ],
    )
