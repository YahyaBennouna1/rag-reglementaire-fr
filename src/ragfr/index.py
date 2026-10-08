"""Construction de l'index : chunking du corpus, embeddings, chargement dans Qdrant.

Une collection Qdrant par méthode de chunking (ex. "fixed-512-64"), pour comparer les méthodes
sans qu'elles s'écrasent. Qdrant tourne ici en mode local (un dossier), sans serveur.
"""

from pathlib import Path

from qdrant_client import QdrantClient, models

from ragfr.chunking.fixed import chunk_fixed
from ragfr.config import ChunkingConfig
from ragfr.embeddings import Embedder
from ragfr.ingestion.models import ParsedDocument
from ragfr.models import Passage

ROOT = Path(__file__).resolve().parents[2]
PARSED_DIR = ROOT / "data" / "parsed"
QDRANT_DIR = ROOT / "data" / "qdrant"


def collection_name(chunking: ChunkingConfig) -> str:
    return f"{chunking.method}-{chunking.size}-{chunking.overlap}"


def load_parsed_documents() -> list[ParsedDocument]:
    paths = sorted(p for p in PARSED_DIR.glob("*.json") if not p.name.endswith(".docling.json"))
    return [ParsedDocument.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def chunk_corpus(chunking: ChunkingConfig) -> list[Passage]:
    if chunking.method != "fixed":
        raise NotImplementedError(f"méthode de chunking pas encore implémentée : {chunking.method}")
    passages = []
    for doc in load_parsed_documents():
        passages.extend(chunk_fixed(doc, chunking.size, chunking.overlap))
    return passages


def get_client() -> QdrantClient:
    return QdrantClient(path=str(QDRANT_DIR))


def build_dense_index(client: QdrantClient, name: str, passages: list[Passage], embedder: Embedder) -> None:
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        name,
        vectors_config=models.VectorParams(size=embedder.dim, distance=models.Distance.COSINE),
    )
    vectors = embedder.encode([p.index_text for p in passages], show_progress=True)
    client.upload_points(
        name,
        points=[
            models.PointStruct(id=i, vector=vec.tolist(), payload=p.model_dump(exclude={"score"}))
            for i, (p, vec) in enumerate(zip(passages, vectors, strict=True))
        ],
    )
