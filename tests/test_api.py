"""Tests de l'API sans LLM ni base : le pipeline est remplacé par des faux."""

import pytest
from fastapi.testclient import TestClient

from ragfr.api import app as api_module
from ragfr.generation import Answer, Citation
from ragfr.models import Passage


def passage(doc_ref: str) -> Passage:
    return Passage(
        id=f"{doc_ref}:1", doc_ref=doc_ref, titre="Guide", page=3, page_end=3, section="2", text="texte"
    )


class FakeSearch:
    def search(self, question, k, dense_query=None):
        return [passage("tls"), passage("docker"), passage("auth-mfa-mdp")][:k]


@pytest.fixture
def client(monkeypatch):
    def fake_answer(cfg, question):
        citation = Citation(phrase="Il faut désactiver TLS 1.0.", passage_id="tls:1", doc_ref="tls", page=3)
        return Answer(
            text="Il faut désactiver TLS 1.0. [P1]",
            sentences=[],
            citations=[citation],
            abstained=False,
            passages=[],
        )

    monkeypatch.setattr(api_module, "answer_question", fake_answer)
    monkeypatch.setattr(api_module, "make_search", lambda cfg: FakeSearch())
    monkeypatch.setattr(api_module, "themes", lambda: {"tls": "authentification", "docker": "conteneurs"})
    monkeypatch.delenv("RAGFR_API_KEY", raising=False)
    api_module._requests.clear()
    return TestClient(api_module.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_renvoie_reponse_et_citations(client):
    r = client.post("/ask", json={"question": "Faut-il garder TLS 1.0 ?"})
    assert r.status_code == 200
    body = r.json()
    assert body["abstention"] is False
    assert body["citations"][0]["doc_ref"] == "tls"


def test_question_trop_courte_refusee(client):
    # Pydantic valide l'entrée : FastAPI répond 422 (« entité non traitable ») sans appeler le pipeline.
    assert client.post("/ask", json={"question": "a"}).status_code == 422


def test_search_filtre_par_theme(client):
    r = client.post("/search", json={"question": "conteneurs", "k": 5, "theme": "conteneurs"})
    assert [p["doc_ref"] for p in r.json()] == ["docker"]


def test_theme_inconnu_refuse(client):
    assert client.post("/search", json={"question": "xyz", "theme": "cuisine"}).status_code == 422


def test_cle_api_exigee_si_definie(client, monkeypatch):
    monkeypatch.setenv("RAGFR_API_KEY", "secret")
    assert client.post("/ask", json={"question": "TLS 1.0 ?"}).status_code == 401
    ok = client.post("/ask", json={"question": "TLS 1.0 ?"}, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200


def test_limite_de_debit(client, monkeypatch):
    monkeypatch.setattr(api_module, "RATE_LIMIT", 2)
    codes = [client.post("/search", json={"question": "TLS 1.0"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_racine_redirige_vers_la_documentation(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/docs"


def test_un_seul_client_qdrant_par_programme(monkeypatch, tmp_path):
    # En mode local, un 2e client sur le même dossier lève une erreur : get_client doit le partager.
    # Dossier temporaire : le test ne dépend pas de l'index du projet (ni d'une évaluation en cours).
    from ragfr import index

    monkeypatch.setattr(index, "QDRANT_DIR", tmp_path)
    index.get_client.cache_clear()
    try:
        assert index.get_client() is index.get_client()
    finally:
        index.get_client().close()
        index.get_client.cache_clear()


def test_qdrant_serveur_si_url_definie(monkeypatch):
    # Avec QDRANT_URL, on se connecte au serveur au lieu d'ouvrir le dossier local.
    # Faux client : le vrai essaierait de joindre le serveur dès sa création (appel réseau).
    from ragfr import index

    created = []
    monkeypatch.setattr(index, "QdrantClient", lambda **kwargs: created.append(kwargs) or object())
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    index.get_client.cache_clear()
    try:
        index.get_client()
        assert created == [{"url": "http://qdrant:6333"}]
    finally:
        index.get_client.cache_clear()
