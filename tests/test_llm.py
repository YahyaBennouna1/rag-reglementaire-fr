"""Tests de llm.py sans aucun appel réseau : litellm.completion est remplacé par un faux."""

from types import SimpleNamespace

import litellm
import pytest
from pydantic import BaseModel

from ragfr import llm


def fake_response(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=2),
    )


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)  # pas d'attente réelle pendant les tests
    return tmp_path


def test_cle_de_cache_stable():
    a = llm._cache_key({"model": "m", "messages": [{"role": "user", "content": "x"}]})
    b = llm._cache_key({"messages": [{"role": "user", "content": "x"}], "model": "m"})
    assert a == b  # l'ordre des clés ne change pas l'empreinte


def test_deuxieme_appel_servi_par_le_cache(isolated_cache, monkeypatch):
    calls = []
    monkeypatch.setattr(litellm, "completion", lambda **kw: calls.append(kw) or fake_response("Paris"))
    messages = [{"role": "user", "content": "Capitale ?"}]

    first = llm.complete(messages, model="fake/model")
    second = llm.complete(messages, model="fake/model")

    assert len(calls) == 1
    assert (first.cached, second.cached) == (False, True)
    assert second.text == "Paris"


def test_reprise_apres_erreur_429(isolated_cache, monkeypatch):
    attempts = []

    def flaky(**kw):
        attempts.append(1)
        if len(attempts) < 3:
            raise litellm.RateLimitError("trop de requêtes", llm_provider="fake", model="fake/model")
        return fake_response("ok")

    monkeypatch.setattr(litellm, "completion", flaky)
    assert llm.complete([{"role": "user", "content": "x"}], model="fake/model").text == "ok"
    assert len(attempts) == 3


def test_json_entre_balises_accepte(isolated_cache, monkeypatch):
    class Route(BaseModel):
        route: str

    monkeypatch.setattr(
        litellm, "completion", lambda **kw: fake_response('```json\n{"route": "simple"}\n```')
    )
    out = llm.complete_json([{"role": "user", "content": "x"}], model="fake/model", schema=Route)
    assert out.route == "simple"
