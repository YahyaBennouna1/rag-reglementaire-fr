"""Copie les collections de l'index local (data/qdrant) vers un serveur Qdrant.

    docker compose up -d qdrant
    uv run python scripts/migrate_qdrant.py --url http://127.0.0.1:6333

127.0.0.1 et pas « localhost » : sous Windows, « localhost » essaie d'abord IPv6 et perd environ
4 secondes par requête (mesuré : 4 120 ms contre 12 ms).

On copie les points tels quels (vecteurs denses, vecteurs BM25, payload) : rien n'est recalculé,
l'index du serveur est identique à l'index local. Relancer le script remplace les collections.
"""

import argparse

from qdrant_client import QdrantClient

from ragfr.index import QDRANT_DIR

BATCH = 256


def copy_collection(source: QdrantClient, target: QdrantClient, name: str) -> int:
    info = source.get_collection(name)
    params = info.config.params
    if target.collection_exists(name):
        target.delete_collection(name)
    # Même configuration : vecteur dense nommé « dense » et vecteur creux « bm25 » (avec IDF).
    target.create_collection(name, vectors_config=params.vectors, sparse_vectors_config=params.sparse_vectors)

    copied, offset = 0, None
    while True:
        # scroll = parcourir la collection page par page (comme un curseur de base de données).
        points, offset = source.scroll(name, limit=BATCH, offset=offset, with_vectors=True, with_payload=True)
        if not points:
            break
        target.upsert(
            name,
            points=[{"id": p.id, "vector": p.vector, "payload": p.payload} for p in points],
        )
        copied += len(points)
        if offset is None:  # plus de page suivante
            break
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:6333")
    args = parser.parse_args()

    source = QdrantClient(path=str(QDRANT_DIR))
    target = QdrantClient(url=args.url)
    for collection in source.get_collections().collections:
        count = copy_collection(source, target, collection.name)
        # Vérification : le serveur doit avoir exactement le même nombre de points.
        on_server = target.count(collection.name, exact=True).count
        status = "OK" if on_server == count else "ÉCART"
        print(f"{collection.name} : {count} points copiés, {on_server} sur le serveur [{status}]")


if __name__ == "__main__":
    main()
