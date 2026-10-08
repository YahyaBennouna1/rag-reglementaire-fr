"""Reciprocal Rank Fusion : fusionner plusieurs listes de résultats par leurs rangs.

    RRF(d) = somme, pour chaque liste où d apparaît, de  poids_liste / (k + rang de d dans cette liste)

On utilise les rangs et pas les scores, car un score BM25 (ex. 14,2) et un cosinus (ex. 0,63)
ne sont pas sur la même échelle : les additionner n'aurait pas de sens.
Les poids (1 par défaut) permettent de faire davantage confiance à un moteur qu'à l'autre.
"""

from ragfr.models import Passage


def reciprocal_rank_fusion(
    result_lists: list[list[Passage]], k: int = 60, weights: list[float] | None = None
) -> list[Passage]:
    weights = weights or [1.0] * len(result_lists)
    if len(weights) != len(result_lists):
        raise ValueError("il faut un poids par liste de résultats")

    scores: dict[str, float] = {}
    passages: dict[str, Passage] = {}
    for results, weight in zip(result_lists, weights, strict=True):
        for rank, passage in enumerate(results, start=1):
            scores[passage.id] = scores.get(passage.id, 0.0) + weight / (k + rank)
            passages.setdefault(passage.id, passage)

    ranked = sorted(scores, key=lambda pid: scores[pid], reverse=True)
    return [passages[pid].model_copy(update={"score": scores[pid]}) for pid in ranked]
