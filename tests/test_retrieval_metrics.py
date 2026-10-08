import math

import pytest

from ragfr.eval.dataset import Reference
from ragfr.eval.retrieval_metrics import covered_refs_by_rank, covers, ndcg_at_k, recall_at_k, reciprocal_rank
from ragfr.models import Passage


def passage(doc_ref: str, text: str) -> Passage:
    return Passage(id="x", doc_ref=doc_ref, titre="t", page=1, page_end=1, section="", text=text)


REF = Reference(doc_ref="tls", page=3, extrait="Il est recommandé de désactiver TLS 1.0")


def test_extrait_contenu_ignore_casse_et_espaces():
    assert covers(passage("tls", "Avant. il est   recommandé de\ndésactiver TLS 1.0 et après."), REF)


def test_mauvais_document_refuse():
    assert not covers(passage("ipsec", "Il est recommandé de désactiver TLS 1.0"), REF)


def test_extrait_coupe_par_une_frontiere_de_chunk():
    assert covers(passage("tls", "Il est recommandé de désactiver"), REF)  # 31/39 caractères
    assert not covers(passage("tls", "Il est"), REF)


def test_metriques_calculees_a_la_main():
    # 2 références ; la n°0 trouvée au rang 2, la n°1 au rang 4.
    found = [set(), {0}, set(), {1}]
    assert recall_at_k(found, n_refs=2, k=2) == 0.5
    assert recall_at_k(found, n_refs=2, k=4) == 1.0
    assert reciprocal_rank(found) == 0.5
    dcg = 1 / math.log2(3) + 1 / math.log2(5)
    ideal = 1 / math.log2(2) + 1 / math.log2(3)
    assert ndcg_at_k(found, n_refs=2, k=10) == pytest.approx(dcg / ideal)


def test_reference_trouvee_deux_fois_comptee_une_fois():
    found = covered_refs_by_rank([passage("tls", REF.extrait), passage("tls", REF.extrait)], [REF])
    assert found == [{0}, {0}]
    assert ndcg_at_k(found, n_refs=1, k=10) == 1.0


def test_rien_trouve():
    assert reciprocal_rank([set(), set()]) == 0.0
    assert recall_at_k([set(), set()], n_refs=1, k=10) == 0.0
