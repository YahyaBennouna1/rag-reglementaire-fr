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


def test_quota_journalier_pas_reessaye(isolated_cache, monkeypatch):
    attempts = []

    def daily_limit(**kw):
        attempts.append(1)
        raise litellm.RateLimitError(
            "Rate limit reached on tokens per day (TPD)", llm_provider="fake", model="fake/model"
        )

    monkeypatch.setattr(litellm, "completion", daily_limit)
    with pytest.raises(litellm.RateLimitError):
        llm.complete([{"role": "user", "content": "x"}], model="fake/model")
    assert len(attempts) == 1  # un quota du jour ne se libère pas en quelques secondes


def test_credits_epuises_pas_reessayes(isolated_cache, monkeypatch):
    attempts = []

    def no_credits(**kw):
        attempts.append(1)
        raise litellm.RateLimitError("You have no credits remaining", llm_provider="openai", model="x")

    monkeypatch.setattr(litellm, "completion", no_credits)
    with pytest.raises(litellm.RateLimitError):
        llm.complete([{"role": "user", "content": "x"}], model="fake/model")
    assert len(attempts) == 1  # sans crédit, réessayer ne sert à rien


def test_cle_de_secours_quand_le_quota_est_epuise(isolated_cache, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "cle-1")
    monkeypatch.setenv("GROQ_API_KEY1", "cle-2")
    used = []

    def by_key(**kw):
        used.append(kw["api_key"])
        if kw["api_key"] == "cle-1":
            raise litellm.RateLimitError("tokens per day (TPD)", llm_provider="groq", model="x")
        return fake_response("ok")

    monkeypatch.setattr(litellm, "completion", by_key)
    assert llm.complete([{"role": "user", "content": "x"}], model="groq/qwen").text == "ok"
    assert used == ["cle-1", "cle-2"]  # une seule tentative sur la clé épuisée, puis la suivante
