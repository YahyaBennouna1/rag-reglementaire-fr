import numpy as np
import pytest
from qdrant_client import QdrantClient

from ragfr.index import build_index
from ragfr.models import Passage
from ragfr.retrieval.bm25 import BM25Retriever
from ragfr.retrieval.dense import DenseRetriever
from ragfr.retrieval.french_analyzer import analyze
from ragfr.retrieval.hybrid import HybridRetriever
from ragfr.retrieval.rrf import reciprocal_rank_fusion


def passage(pid: str, text: str = "texte") -> Passage:
    return Passage(id=pid, doc_ref=pid.split(":")[0], titre="t", page=1, page_end=1, section="", text=text)


# --- Analyseur français ---------------------------------------------------------


def test_minuscules_accents_racines():
    assert analyze("Recommandations") == analyze("recommandée") == ["recommand"]
    assert analyze("SÉCURITÉ") == analyze("sécurité")
    # Limite connue : sans accents, le raciniseur français ne retrouve pas la même racine.
    assert analyze("securite") != analyze("sécurité")


def test_mots_vides_retires():
    assert analyze("le chiffrement de la sauvegarde") == analyze("chiffrement sauvegarde")


def test_codes_gardes_intacts():
    assert analyze("Voir R12 et ANSSI-PA-022 pour le 802.1X") == ["voir", "r12", "anssi-pa-022", "802.1x"]


# --- RRF : un cas calculé à la main -----------------------------------------------


def test_rrf_calcule_a_la_main():
    bm25 = [passage("a:1"), passage("b:1"), passage("c:1")]
    dense = [passage("b:1"), passage("d:1")]
    fused = reciprocal_rank_fusion([bm25, dense], k=60)

    # b : 1/(60+2) + 1/(60+1) = 0,03252 ; a : 1/61 = 0,01639 ; d : 1/62 = 0,01613 ; c : 1/63 = 0,01587
    assert [p.id for p in fused] == ["b:1", "a:1", "d:1", "c:1"]
    assert fused[0].score == pytest.approx(1 / 62 + 1 / 61)
    assert fused[3].score == pytest.approx(1 / 63)


# --- BM25 et hybride de bout en bout, dans un Qdrant en mémoire --------------------


class FakeEmbedder:
    """Faux modèle d'embedding : 4 dimensions, un axe par sujet. Pas de téléchargement."""

    dim = 4
    TOPICS = ["mot de passe", "conteneur", "journal", "chiffrement"]

    def encode(self, texts, kind="passage", show_progress=False):
        rows = []
        for text in texts:
            vec = np.array([1.0 if topic in text.lower() else 0.0 for topic in self.TOPICS]) + 0.01
            rows.append(vec / np.linalg.norm(vec))
        return np.array(rows, dtype=np.float32)


@pytest.fixture
def corpus():
    client = QdrantClient(":memory:")
    # Comme dans les vrais guides, « recommandé » est partout : il est peu informatif (IDF faible).
    passages = [
        passage("auth:1", "Un mot de passe robuste de 12 caractères est recommandé."),
        passage("docker:1", "Chaque conteneur doit avoir un réseau dédié, voir R12."),
        passage("logs:1", "Il est recommandé d'horodater le journal des évènements."),
        passage("crypto:1", "Le chiffrement des sauvegardes est recommandé."),
    ]
    build_index(client, "test", passages, FakeEmbedder())
    return client


def test_bm25_trouve_le_code_exact(corpus):
    results = BM25Retriever(corpus, "test").search("Que dit la recommandation R12 ?", k=2)
    assert results[0].id == "docker:1"


def test_hybride_combine_les_deux_moteurs(corpus):
    hybrid = HybridRetriever(
        BM25Retriever(corpus, "test"), DenseRetriever(corpus, "test", FakeEmbedder()), candidates=4
    )
    results = hybrid.search("longueur minimale d'un mot de passe", k=4)
    assert results[0].id == "auth:1"
    assert len({p.id for p in results}) == len(results)  # pas de doublon après fusion


def test_integration_hyde_sur_les_vrais_moteurs(corpus, monkeypatch):
    """Assemble les VRAIS moteurs : un paramètre oublié entre deux briques ferait planter ce test."""
    from ragfr.query import transforms
    from ragfr.retrieval.reranker import RerankingRetriever

    class FakeReranker:
        def rerank(self, query, passages, top_n):
            return passages[:top_n]

    monkeypatch.setattr(
        transforms, "hypothetical_answer", lambda q, m: "Un mot de passe robuste est recommandé."
    )
    hybrid = HybridRetriever(
        BM25Retriever(corpus, "test"), DenseRetriever(corpus, "test", FakeEmbedder()), candidates=4
    )
    search = transforms.TransformingRetriever(
        RerankingRetriever(hybrid, FakeReranker(), candidates=4), router=False, hyde=True, model="faux"
    )
    results = search.search("longueur minimale d'un mot de passe", k=2)
    assert results[0].id == "auth:1"
