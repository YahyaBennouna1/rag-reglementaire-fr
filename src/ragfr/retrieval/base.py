from typing import Protocol

from ragfr.models import Passage


class Retriever(Protocol):
    """Tout moteur de recherche du projet respecte cette interface (dense, BM25, hybride, graphe).

    On peut donc les échanger dans le YAML sans toucher au reste du code.
    """

    def search(self, query: str, k: int) -> list[Passage]: ...
