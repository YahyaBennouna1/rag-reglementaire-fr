"""Construit l'index décrit par une config : chunking du corpus, embeddings, collection Qdrant.

uv run python scripts/build_index.py --config configs/baseline.yaml
"""

import argparse
import time

from ragfr.config import load_config
from ragfr.index import build_index, chunk_corpus, collection_name, get_client
from ragfr.pipeline import get_embedder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True)
    cfg = load_config(parser.parse_args().config)

    start = time.perf_counter()
    passages = chunk_corpus(cfg.chunking)
    name = collection_name(cfg.chunking)
    print(f"{len(passages)} passages ({sum(p.is_table for p in passages)} tableaux) -> collection {name}")

    build_index(get_client(), name, passages, get_embedder())
    print(f"Index construit en {time.perf_counter() - start:.0f} s")


if __name__ == "__main__":
    main()
