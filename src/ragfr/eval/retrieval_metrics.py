"""Métriques de recherche : recall@k, MRR, nDCG@k.

Un passage trouvé « couvre » une référence s'il vient du bon guide et contient l'essentiel de
l'extrait de référence. On compte au niveau des références, pas des chunks : avec des chunks
qui se chevauchent, un même extrait peut apparaître dans deux chunks, et il ne doit compter qu'une fois.
"""

import math
import re
from difflib import SequenceMatcher

from ragfr.eval.dataset import Reference
from ragfr.models import Passage

MIN_COVERAGE = 0.6  # part de l'extrait qui doit se retrouver d'un seul tenant dans le passage


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def covers(passage: Passage, ref: Reference) -> bool:
    if passage.doc_ref != ref.doc_ref:
        return False
    extrait, texte = normalize(ref.extrait), normalize(passage.text)
    if extrait in texte:
        return True
    # L'extrait peut être coupé par une frontière de chunk : on accepte un long morceau commun.
    match = SequenceMatcher(None, extrait, texte, autojunk=False).find_longest_match()
    return match.size >= MIN_COVERAGE * len(extrait)


def covered_refs_by_rank(passages: list[Passage], refs: list[Reference]) -> list[set[int]]:
    """Pour chaque rang, l'ensemble des numéros de références couvertes par ce passage."""
    return [{i for i, ref in enumerate(refs) if covers(p, ref)} for p in passages]


def recall_at_k(found: list[set[int]], n_refs: int, k: int) -> float:
    covered = set().union(*found[:k]) if found[:k] else set()
    return len(covered) / n_refs


def reciprocal_rank(found: list[set[int]]) -> float:
    for rank, refs in enumerate(found, start=1):
        if refs:
            return 1 / rank
    return 0.0


def ndcg_at_k(found: list[set[int]], n_refs: int, k: int) -> float:
    seen: set[int] = set()
    dcg = 0.0
    for rank, refs in enumerate(found[:k], start=1):
        new = refs - seen  # une référence ne rapporte qu'une fois
        if new:
            dcg += len(new) / math.log2(rank + 1)
            seen |= new
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(n_refs, k) + 1))
    # Un passage peut couvrir deux références d'un coup et dépasser l'idéal « une par rang » : on plafonne.
    return min(1.0, dcg / ideal)
