"""Tests de l'agent : les LLM et la recherche sont remplacés par des faux, on teste la logique du graphe."""

import pytest

from ragfr.agent import graph as agent_module
from ragfr.agent.graph import Grade, Rewrite, build_agent
from ragfr.config import Config
from ragfr.generation import Answer
from ragfr.models import Passage


def passage(pid: str) -> Passage:
    return Passage(id=pid, doc_ref="doc", titre="Guide test", page=1, page_end=1, section="", text="texte")


class FakeRetriever:
    def __init__(self):
        self.queries = []

    def search(self, query, k, dense_query=None):
        self.queries.append(query)
        return [passage("doc:1"), passage("doc:2")]


@pytest.fixture
def run(monkeypatch):
    """Lance l'agent avec une suite de verdicts imposés au juge ; renvoie (état final, requêtes cherchées)."""

    def _run(verdicts: list[str]):
        verdicts = list(verdicts)

        def fake_complete_json(messages, model, schema, **kwargs):
            if schema is Grade:
                return Grade(grade=verdicts.pop(0), useful=["P1"], missing="la durée de conservation")
            if schema is Rewrite:
                return Rewrite(question="requête reformulée")
            raise AssertionError(f"schéma inattendu : {schema}")

        def fake_generate(question, passages, model, temperature):
            return Answer(text="réponse", sentences=[], citations=[], abstained=False, passages=passages)

        monkeypatch.setattr(agent_module, "complete_json", fake_complete_json)
        monkeypatch.setattr(agent_module, "generate_answer", fake_generate)
        retriever = FakeRetriever()
        cfg = Config(name="test", agent={"enabled": True, "max_rewrites": 2})
        state = build_agent(cfg, retriever).invoke({"question": "Combien de temps garder les journaux ?"})
        return state, retriever.queries

    return _run


def test_passages_suffisants_on_repond(run):
    state, queries = run(["suffisant"])
    assert state["answer"].text == "réponse"
    assert queries == ["Combien de temps garder les journaux ?"]
    assert [p.id for p in state["passages"]] == ["doc:1"]  # seuls les passages jugés utiles


def test_reformulation_puis_reponse(run):
    state, queries = run(["insuffisant", "suffisant"])
    assert state["answer"].abstained is False
    assert queries == ["Combien de temps garder les journaux ?", "requête reformulée"]
    assert state["rewrites"] == 1


def test_abstention_apres_deux_reformulations(run):
    state, queries = run(["insuffisant", "partiel", "insuffisant"])
    assert state["answer"].abstained is True
    assert "Je ne sais pas" in state["answer"].text
    assert "Guide test" in state["answer"].text  # propose les documents les plus proches
    assert len(queries) == 3  # 1 recherche + 2 relances, pas plus
